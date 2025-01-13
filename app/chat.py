from typing import Dict, Optional, List

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, Tags
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from cl_helpers import chat_ctx_to_openai_history
from vector_stores import get_chroma

embeddings = OpenAIEmbeddings()


@cl.on_message
async def on_message(message: cl.Message):
    # Get all the messages in the conversation in the OpenAI format
    user: cl.User = cl.user_session.get("user")

    user_id = user.to_dict().get('id')
    print('user id is ' + user_id)

    chroma = get_chroma(embeddings, user_id)
    # db_records = chroma.get()
    # print(db_records['documents'])
    message_history = chat_ctx_to_openai_history(cl.chat_context)
    # TODO: change to some other mem
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )
    # chain: ConversationalRetrievalChain = cl.user_session.get("chain")
    # TODO: use RetrievalQA
    chain = ConversationalRetrievalChain.from_llm(
        ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True),
        chain_type="stuff",
        retriever=chroma.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )
    print(cl.user_session.get("id"))
    cb = cl.AsyncLangchainCallbackHandler()

    res = await chain.acall(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents: List[Document] = res["source_documents"]

    text_elements: List[cl.Text] = []

    # if source_documents:
    #     for source_idx, source_doc in enumerate(source_documents):
    #         source_name = f"source_{source_idx}"
    #         # Create the text element referenced in the message
    #         text_elements.append(
    #             cl.Text(
    #                 content=source_doc.page_content, name=source_name, display="side"
    #             )
    #         )
    #     source_names = [text_el.name for text_el in text_elements]
    #
    #     if source_names:
    #         answer += f"\nSources: {', '.join(source_names)}"
    #     else:
    #         answer += "\nNo sources found"

    await cl.Message(content=answer, elements=text_elements).send()


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
        content=f"Select docs [for all](http://localhost/gdocs) chats "
                f"or for [this](http://localhost/{thread_id}/gdocs) chat only.",
        # actions=actions
    ).send())

    # settings = init_settings()
    # await settings.send()


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


@cl.action_callback("action_button_1")
async def on_action_1(action: cl.Action):
    session_id = cl.user_session.get("id")
    await cl.Message(content=f"Executed {action.name} [go](http://localhost/gdocs/{session_id})").send()
    # Optionally remove the action button from the chatbot user interface
    # await action.remove()


@cl.action_callback("action_button_2")
async def on_action_2(action: cl.Action):
    print(cl.user_session.get("id"))
    await cl.Message(content=f"Executed {action.name} [go](http://localhost/gdocs)").send()
    # Optionally remove the action button from the chatbot user interface
    # await action.remove()


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
