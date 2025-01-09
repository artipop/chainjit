from typing import Annotated, Union

import chainlit as cl
from chainlit.auth import authenticate_user
from chainlit.context import init_http_context, init_ws_context
from chainlit.session import WebsocketSession
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, Depends
from fastapi.responses import (
    HTMLResponse,
)
from fastapi.security import APIKeyCookie
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI()

cookie_scheme = APIKeyCookie(name="access_token")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)


@app.get("/app")
def read_main(token: Annotated[str, Depends(cookie_scheme)]):
    print(token)
    return {"message": "Hello World from main app"}


@app.get("/gdocs")
async def list_docs(
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')
    creds = Credentials(token=token)
    try:
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=10, fields="nextPageToken,files(id,name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")
    return HTMLResponse("Hello World")


@app.get("/gdocs/{session_id}/{doc_id}")
async def upload_doc(
        doc_id: str,
        session_id: str,
        current_user: Annotated[
            Union[cl.User], Depends(authenticate_user)
        ],
):
    # init both contexts, because we need token from http oauth callback,
    # and we should pass `chain` to the websocket session. TODO: maybe we can use persistence instead
    ws_session = WebsocketSession.get_by_id(session_id=session_id)
    init_ws_context(ws_session)
    init_http_context(user=current_user)
    token = current_user.metadata.get('token')
    creds = Credentials(token=token)
    try:
        service = build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()
        content = document.get('body').get('content')
        full_text = extract_text(content)
        texts = text_splitter.split_text(full_text)

        # Create a metadata for each chunk
        metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]

        # Create a Chroma vector store
        embeddings = OpenAIEmbeddings()
        docsearch = await cl.make_async(Chroma.from_texts)(
            texts, embeddings, metadatas=metadatas,
            # TODO: add ref to doc_id? and fill other parameters
            # ids=[doc_id]
        )

        message_history = ChatMessageHistory()

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            chat_memory=message_history,
            return_messages=True,
        )

        # Create a chain that uses the Chroma vector store
        chain = ConversationalRetrievalChain.from_llm(
            ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True),
            chain_type="stuff",
            retriever=docsearch.as_retriever(),
            memory=memory,
            return_source_documents=True,
        )
        cl.user_session.set("chain", chain)
    except HttpError as err:
        print(err)
    return "ok"


def extract_text(elements):
    text = ''
    for element in elements:
        if 'paragraph' in element:
            for run in element['paragraph']['elements']:
                if 'textRun' in run:
                    text += run['textRun']['content']
        elif 'table' in element:
            for row in element['table']['tableRows']:
                for cell in row['tableCells']:
                    text += extract_text(cell['content'])
        elif 'tableOfContents' in element:
            text += extract_text(element['tableOfContents']['content'])
    return text


mount_chainlit(app=app, target="chat.py", path="/chat")
