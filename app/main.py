from typing import Annotated, Union

import chainlit as cl
from chainlit.auth import authenticate_user
from chainlit.context import init_http_context
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, Depends, Request
from fastapi.responses import (
    HTMLResponse, FileResponse
)
from fastapi.security import APIKeyCookie
from fastapi.templating import Jinja2Templates
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from starlette.responses import RedirectResponse

from lc_helpers import get_llm
from gdoc_service import gdoc_content_by_id, list_all_gdocs
from vector_stores import create_chroma

app = FastAPI()
templates = Jinja2Templates(directory="templates")
cookie_scheme = APIKeyCookie(name="access_token")

embeddings = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)


@app.get("/app")
def read_main(token: Annotated[str, Depends(cookie_scheme)]):
    print(token)
    return {"message": "Hello World from main app"}


@app.get("/")
def read_index():
    return FileResponse('static/index.html')


@app.get("/privacy")
async def read_privacy_policy():
    return FileResponse('static/privacy.html')


def map_item(item):
    return {'name': item['name'], 'id': item['id'], 'is_enabled': False}


@app.get("/{thread_id}/gdocs")
async def list_docs(
        request: Request,
        thread_id: str,
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    print('chat ' + thread_id)
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')


@app.get("/gdocs")
async def list_docs(
        request: Request,
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')
    items = await list_all_gdocs(token)
    if not items:
        print("No files found.")
        return HTMLResponse("void")
    print("Files:")
    for item in items:
        print(f"{item['name']} ({item['id']})")
    return templates.TemplateResponse("select_docs.html",
                                      {"request": request, "records": [map_item(it) for it in items]})


@app.get("/gdocs/{doc_id}")
async def upload_doc(
        doc_id: str,
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')
    texts, metadatas = await load_doc(doc_id, token)
    user_id = current_user.to_dict().get('id')
    chain = await create_user_chain(texts, metadatas, user_id)
    cl.user_session.set("chain", chain)

    # TODO: use persistence instead of in-mem session:
    # identifier = current_user.identifier
    # connection = "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"  # Uses psycopg3!
    # vector_store = PGVector(
    #     embedding_function=embeddings,
    #     collection_name=identifier,
    #     connection_string=connection,
    #     use_jsonb=True,
    # )
    return "ok"


@app.post("/gdocs/save")
async def save_records(
        request: Request,
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')
    data = await request.json()
    t: list[str] = []
    m: list[dict[str, str]] = []
    for item in data:
        doc_id = item["id"]
        texts, metadatas = await load_doc(doc_id, token)
        # or we can use Chroma.add_text
        t.extend(texts)
        m.extend(metadatas)
    user_id = current_user.to_dict().get('id')
    chain = await create_user_chain(t, m, user_id)
    cl.user_session.set("chain", chain)
    return {"message": "Данные успешно сохранены"}


async def create_user_chain(texts, metadatas, user_id):
    print('user id is ' + user_id)
    chroma = await cl.make_async(create_chroma)(embeddings, texts, metadatas, user_id)
    message_history = InMemoryChatMessageHistory()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )
    return ConversationalRetrievalChain.from_llm(
        get_llm(),
        chain_type="stuff",
        retriever=chroma.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )


async def load_doc(doc_id, token):
    full_text = await gdoc_content_by_id(doc_id, token)
    texts = text_splitter.split_text(full_text)
    # Create a metadata for each chunk
    metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]
    return texts, metadatas


mount_chainlit(app=app, target="chat.py", path="/dok")
