from typing import Dict, Optional

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, Tags

from cl_helpers import chat_ctx_to_openai_history
from rags import rag_pipe


@cl.on_message
async def on_message(message: cl.Message):
    # Get all the messages in the conversation in the OpenAI format
    user: cl.User = cl.user_session.get("user")
    user_id = user.to_dict().get('id')
    session_id = cl.user_session.get("id")
    _ = chat_ctx_to_openai_history(cl.chat_context)
    response_text, sources = rag_pipe(message.content, user_id)
    formatted_response = f"""
    {response_text}

    Sources: {sources}
"""
    await cl.Message(content=formatted_response).send()


@cl.set_starters
async def set_starters():
    return init_starters()


@cl.on_chat_start
async def on_chat_start():
    thread_id = cl.context.session.thread_id
    session_id = cl.user_session.get("id")

    actions = init_actions(session_id)
    # TODO: do not create new chat with only one message every time...
    await (cl.Message(
        content=f"Select docs [for all](/gdocs) chats "
                f"or for [this](/{thread_id}/gdocs) chat only.",
        # actions=actions
    ).send())

    # documents = [
    #     {"name": "Документ 1", "url": "https://example.com/doc1", "checked": False},
    #     {"name": "Документ 2", "url": "https://example.com/doc2", "checked": False},
    #     {"name": "Документ 3", "url": "https://example.com/doc3", "checked": False},
    # ]
    # custom_element = cl.CustomElement(
    #     name="DocumentsList",
    #     props={"documents": documents},
    #     display="inline",
    # )
    # await cl.Message(
    #     content="Вот список документов:",
    #     elements=[custom_element],
    # ).send()
    # settings = init_settings()
    # await settings.send()


# @cl.action_callback("send_documents")
async def handle_send_documents(event):
    documents = event["data"]
    selected_docs = [doc for doc in documents if doc["checked"]]

    # Логика обработки выбранных документов
    if selected_docs:
        doc_names = ", ".join(doc["name"] for doc in selected_docs)
        await cl.Message(content=f"Вы выбрали документы: {doc_names}").send()
    else:
        await cl.Message(content="Вы не выбрали ни одного документа.").send()


@cl.on_chat_resume
async def on_chat_resume(thread):
    thread_id = thread.get("id")


# noinspection PyUnusedLocal
@cl.oauth_callback
def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: Dict[str, str],
        default_user: cl.User,
) -> Optional[cl.User]:
    default_user.metadata['token'] = token
    return default_user


def init_starters():
    return [
        cl.Starter(
            label="Example",
            message="Find the receipt of my favourite apple pie.",
            icon="/public/example.png"
        )
    ]


def init_settings():
    return cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
                initial_index=1,
            ),
            Tags(id="StopSequence", label="OpenAI - StopSequence", initial=["uno", "dos"],
                 values=["uno", "dos", "tres"]),
            Switch(id="Streaming7", label="OpenAI - Stream Tokens", initial=True),
            Slider(
                id="Temperature",
                label="OpenAI - Temperature",
                initial=0,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="SAI_Steps",
                label="Stability AI - Steps",
                initial=30,
                min=10,
                max=150,
                step=1,
                description="Amount of inference steps performed on image generation.",
            ),
            Slider(
                id="SAI_Cfg_Scale",
                label="Stability AI - Cfg_Scale",
                initial=7,
                min=1,
                max=35,
                step=0.1,
                description="Influences how strongly your generation is guided to match your prompt.",
            ),
            Slider(
                id="SAI_Width",
                label="Stability AI - Image Width",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
            Slider(
                id="SAI_Height",
                label="Stability AI - Image Height",
                initial=512,
                min=256,
                max=2048,
                step=64,
                tooltip="Measured in pixels",
            ),
        ]
    )


def init_actions(session_id):
    return [
        cl.Action(
            name="action_button_1",
            icon="mouse-pointer-click",
            payload={"session_id": session_id},
            label="Only this chat"
        ),
        cl.Action(
            name="action_button_2",
            icon="mouse-pointer-click",
            payload={"value": "example_value"},
            label="All chats"
        ),
    ]
