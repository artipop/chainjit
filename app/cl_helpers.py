from chainlit.chat_context import ChatContext
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.messages import ChatMessage


def chat_ctx_to_openai_history(chat_context: ChatContext) -> BaseChatMessageHistory:
    messages = chat_context.to_openai()
    # noinspection PyArgumentList
    return InMemoryChatMessageHistory(
        messages=[ChatMessage(content=m.get('content'), role=m.get('role')) for m in messages])
