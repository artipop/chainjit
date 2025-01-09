from typing import Annotated, Union

from fastapi import FastAPI, Depends, Request
from fastapi.responses import (
    HTMLResponse,
)
from fastapi.security import APIKeyCookie
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import chainlit as cl
from chainlit.auth import authenticate_user
from chainlit.utils import mount_chainlit

app = FastAPI()

cookie_scheme = APIKeyCookie(name="access_token")


@app.get("/app")
def read_main(token: Annotated[str, Depends(cookie_scheme)]):
    print(token)
    return {"message": "Hello World from main app"}


@app.get("/gdocs")
async def list_docs(
    request: Request,
    current_user: Annotated[
        Union[cl.User], Depends(authenticate_user)
    ],
):
    # init_http_context(user=current_user)
    # await cl.Message(content="Hello World").send()
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


@app.post("/gdocs/{doc_id}")
async def upload_doc(
    doc_id: str,
    request: Request,
    current_user: Annotated[
        Union[cl.User], Depends(authenticate_user)
    ],
):
    token = current_user.metadata.get('token')
    creds = Credentials(token=token)
    try:
        service = build("docs", "v1", credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()
        content = document.get('body').get('content')
        full_text = extract_text(content)
        print(full_text)
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
