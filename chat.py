from typing import Dict, Optional, List

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, Tags
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_core.documents import Document


@cl.on_message
async def on_message(message: cl.Message):
    # Get all the messages in the conversation in the OpenAI format
    # print(cl.chat_context.to_openai())

    chain: ConversationalRetrievalChain = cl.user_session.get("chain")
    print(cl.user_session.get("id"))
    cb = cl.AsyncLangchainCallbackHandler()

    res = await chain.acall(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents: List[Document] = res["source_documents"]

    text_elements: List[cl.Text] = []

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            # Create the text element referenced in the message
            text_elements.append(
                cl.Text(
                    content=source_doc.page_content, name=source_name, display="side"
                )
            )
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"

    await cl.Message(content=answer, elements=text_elements).send()


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


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Example",
            message="Find the receipt of my favourite apple pie.",
            icon="/public/example.png"
        )
    ]


@cl.on_chat_start
async def start():
    # TODO!!! pass it somehow
    print(cl.user_session.get("id"))
    settings = cl.ChatSettings(
        [
            Select(
                id="Model",
                label="OpenAI - Model",
                values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
                initial_index=1,
            ),
            Tags(id="StopSequence", label="OpenAI - StopSequence", initial=["uno", "dos"], values=["uno", "dos", "tres"]),
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
    await settings.send()
