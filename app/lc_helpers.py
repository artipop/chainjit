from os import environ

from langchain_openai import OpenAIEmbeddings, ChatOpenAI


def get_embeddings():
    return OpenAIEmbeddings(openai_api_base=environ.get("OPENAI_API_URL"))


def get_llm():
    return ChatOpenAI(openai_api_base=environ.get("OPENAI_API_URL"), model_name="gpt-4o", temperature=0, streaming=True)
