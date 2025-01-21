from typing import Dict, Optional

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, Tags

from cl_helpers import chat_ctx_to_openai_history
from rags import rag_pipe, get_rag_docs_ids


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
async def set_starters(user: cl.User):
    return init_starters()


# @cl.set_chat_profiles()
# def set_chat_profiles(user: cl.User):


@cl.on_chat_start
async def on_chat_start():
    thread_id = cl.context.session.thread_id
    session_id = cl.user_session.get("id")
    actions = init_actions(session_id)
    user: cl.User = cl.user_session.get("user")
    user_id = user.to_dict().get('id')
    await (cl.Message(
        # content=f"Select Google docs for",
        content=f"Выберите Google документы для",
        actions=actions
    ).send())
    # settings = init_settings()
    # await settings.send()


# @cl.action_callback("send_documents")
# async def handle_send_documents(event):
#     documents = event["data"]
#     selected_docs = [doc for doc in documents if doc["checked"]]
#
#     # Логика обработки выбранных документов
#     if selected_docs:
#         doc_names = ", ".join(doc["name"] for doc in selected_docs)
#         await cl.Message(content=f"Вы выбрали документы: {doc_names}").send()
#     else:
#         await cl.Message(content="Вы не выбрали ни одного документа.").send()


@cl.action_callback("select_shared_docs")
async def on_select_shared_docs(action: cl.Action):
    custom_element = cl.CustomElement(
        name="DocumentPage",
        # props={"documents": documents},
        display="inline",
    )
    await cl.Message(
        content="Список ваших документов:",
        elements=[custom_element],
    ).send()
    # Optionally remove the action button from the chatbot user interface
    # await action.remove()


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


def init_actions(session_id):
    return [
        # cl.Action(
        #     name="action_button_1",
        #     icon="mouse-pointer-click",
        #     payload={"session_id": session_id},
        #     label="Only this chat"
        # ),
        cl.Action(
            name="select_shared_docs",
            icon="mouse-pointer-click",
            payload={"value": "example_value"},
            # label="all chats"
            label="всех чатов"
        ),
    ]
