"""LangGraph node functions for the CRAG pipeline."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from pydantic import BaseModel, Field

from graph.state import CRAGState, GradeResult

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"
GRADE_THRESHOLD = 0.7
MAX_ITERATIONS = 2


class GradeOutput(BaseModel):
    """Structured output schema for the relevance grader LLM call."""

    relevant: bool = Field(description="Whether the document is relevant to the query")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score between 0.0 and 1.0")
    reason: str = Field(description="Brief explanation of the relevance decision")


def _get_retriever():
    """Return a Chroma vectorstore for the crag_corpus collection."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    return vectorstore


def retrieve(state: CRAGState) -> dict:
    """
    Retrieve the top-5 most similar documents for the active query.

    Uses reformulated_query if set, otherwise falls back to the original query.
    Returns: {"retrieved_docs": list[Document]}
    """
    active_query = state.get("reformulated_query") or state["query"]
    vectorstore = _get_retriever()
    docs = vectorstore.similarity_search(active_query, k=5)
    return {"retrieved_docs": docs}


def grade_documents(state: CRAGState) -> dict:
    """
    Grade each retrieved document for relevance to the active query.

    Calls gpt-4o-mini once per document via structured output.
    Sets relevant=True iff score >= 0.7 (Python-computed, not trusted from LLM).
    Returns: {"grade_results": list[GradeResult]}
    """
    active_query = state.get("reformulated_query") or state["query"]
    docs: list[Document] = state["retrieved_docs"]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    grader = llm.with_structured_output(GradeOutput)

    grade_results: list[GradeResult] = []
    for i, doc in enumerate(docs):
        prompt = (
            f"You are a relevance grader. Given the following document and query, "
            f"rate the document's relevance on a scale of 0.0 to 1.0.\n\n"
            f"Query: {active_query}\n\n"
            f"Document: {doc.page_content}"
        )
        output: GradeOutput = grader.invoke(prompt)
        grade_results.append(
            GradeResult(
                doc_id=f"{doc.metadata.get('source', 'unknown')}_{i}",
                score=output.score,
                relevant=output.score >= GRADE_THRESHOLD,
                reason=output.reason,
            )
        )

    return {"grade_results": grade_results}


def reformulate_query(state: CRAGState) -> dict:
    """
    Reformulate the query using the reason from the best-scoring failed GradeResult.

    Increments iteration_count.
    Returns: {"reformulated_query": str, "iteration_count": int}
    """
    original_query = state["query"]
    grade_results: list[GradeResult] = state.get("grade_results", [])

    # Find the reason from the highest-scoring (but still failing) grade result
    if grade_results:
        best_failed = max(grade_results, key=lambda r: r["score"])
        reason = best_failed["reason"]
    else:
        reason = ""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Original query: {original_query}\n"
        f"Reason the documents were not relevant: {reason}\n"
        f"Reformulate the query to better retrieve relevant documents. "
        f"Return only the reformulated query string, nothing else."
    )
    response = llm.invoke(prompt)
    new_query = response.content.strip()

    return {
        "reformulated_query": new_query,
        "iteration_count": state["iteration_count"] + 1,
    }


def generate(state: CRAGState) -> dict:
    """
    Generate a final answer using only documents that scored >= 0.7.

    Returns: {"final_answer": str}
    """
    docs: list[Document] = state["retrieved_docs"]
    grade_results: list[GradeResult] = state["grade_results"]

    # Filter docs to those with passing grade scores (index-aligned with grade_results)
    passing_docs = [
        doc for doc, grade in zip(docs, grade_results)
        if grade["score"] >= GRADE_THRESHOLD
    ]

    if not passing_docs:
        # Defensive guard — routing should prevent this
        return {"final_answer": "Unable to generate answer: no relevant context."}

    context = "\n\n".join(doc.page_content for doc in passing_docs)
    active_query = state.get("reformulated_query") or state["query"]

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = (
        f"You are a helpful assistant. Answer the question using only the provided context. "
        f"If the context does not contain the answer, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {active_query}"
    )
    response = llm.invoke(prompt)
    return {"final_answer": response.content.strip()}


def not_found(state: CRAGState) -> dict:
    """
    Build a structured refusal response when all reformulation attempts are exhausted.

    Returns: {"final_answer": str}
    """
    grade_results: list[GradeResult] = state.get("grade_results", [])

    if grade_results:
        best = max(grade_results, key=lambda r: r["score"])
    else:
        best = GradeResult(doc_id="", score=0.0, relevant=False, reason="no documents retrieved")

    final_answer = (
        f"I couldn't find relevant information in the knowledge base. "
        f"(Best relevance score: {best['score']:.2f} — reason: '{best['reason']}')"
    )
    return {"final_answer": final_answer}


def route_after_grading(state: CRAGState) -> str:
    """
    Pure routing function for the conditional edge after grade_documents.

    Returns:
        "generate"          — at least one GradeResult has score >= 0.7
        "reformulate_query" — zero passing docs AND iteration_count < 2
        "not_found"         — zero passing docs AND iteration_count >= 2
    """
    passing = [r for r in state["grade_results"] if r["score"] >= GRADE_THRESHOLD]
    if passing:
        return "generate"
    if state["iteration_count"] < MAX_ITERATIONS:
        return "reformulate_query"
    return "not_found"
