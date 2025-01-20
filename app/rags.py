from langchain_core.prompts import ChatPromptTemplate

from app.lc_helpers import get_llm, get_embeddings
from app.vector_stores import get_chroma

PROMPT_TEMPLATE = """
Answer the question based only on the following context:
{context}
 - -
Answer the question based on the above context: {question}
"""


def rag_pipe(query_text, user_id):
    embeddings = get_embeddings()
    db = get_chroma(embeddings, user_id + '-docs')
    llm = get_llm()
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")
    context_text = "\n\n - -\n\n".join([doc.page_content for doc, _score in results])
    # Create prompt template using context and query text
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    response_text = llm.predict(prompt)
    # Get sources of the matching documents
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    return response_text, sources


# def retrieval_rag_pipe(query_text, user_id):
#     embeddings = get_embeddings()
#     db = get_chroma(embeddings, user_id + '-docs')
#     llm = get_llm()
#     qa_chain = (
#             {
#                 "context": db.as_retriever() | format_docs,
#                 "question": RunnablePassthrough(),
#             }
#             | prompt
#             | llm
#             | StrOutputParser()
#     )
#     qa_chain.invoke(query_text)
