from typing import List

import chainlit as cl
from chainlit.chat_context import ChatContext
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import ChatMessage


def chat_ctx_to_openai_history(chat_context: ChatContext) -> BaseChatMessageHistory:
    messages = chat_context.to_openai()
    # noinspection PyArgumentList
    return InMemoryChatMessageHistory(
        messages=[ChatMessage(content=m.get('content'), role=m.get('role')) for m in messages])


def sources_as_elements(source_documents: List[Document]):
    """
    Usage:
    ```python
    cb = cl.AsyncLangchainCallbackHandler()
    res = await chain.acall(query_text, callbacks=[cb])
    answer = res["answer"]
    source_names = sources_as_elements(res["source_documents"])
    if source_names:
        answer += f"\nSources: {', '.join(source_names)}"
    else:
        answer += "\nNo sources found"
    await cl.Message(content=answer, elements=text_elements).send()
    ```
    """
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
        return source_names
