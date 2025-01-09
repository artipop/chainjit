from typing import Dict, Optional

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, Tags


@cl.on_message
async def on_message(message: cl.Message):
    get = cl.user_session.get("user")
    print(get)
    # Get all the messages in the conversation in the OpenAI format
    print(cl.chat_context.to_openai())

    # Send the response
    response = f"Hello, you just sent: {message.content}!"
    await cl.Message(response).send()


# TODO: add scopes and set up to use cookie or use header when accessing an API
# noinspection PyUnusedLocal
@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
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
