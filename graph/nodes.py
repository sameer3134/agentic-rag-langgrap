"""LangGraph node functions — built via make_nodes() factory for per-user collection isolation."""
from __future__ import annotations

import os
from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from graph.state import CRAGState, GradeResult

RELEVANCE_THRESHOLD = 0.7
MAX_ITERATIONS = 2
RETRIEVAL_K = 5


class _DocGrade(BaseModel):
    score: float = Field(description="Relevance score 0.0–1.0")
    reason: str = Field(description="One sentence explanation of the score")


def make_nodes(collection_name: str) -> dict[str, Any]:
    """Return a dict of node callables, all scoped to the given Chroma collection."""
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
    )

    grader = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(_DocGrade)
    reformulator = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    generator = ChatOpenAI(model="gpt-4o", temperature=0.1)

    def retrieve(state: CRAGState) -> dict:
        query = state.get("reformulated_query") or state["query"]
        docs = vectorstore.similarity_search(query, k=RETRIEVAL_K)
        return {"retrieved_docs": docs}

    def grade_documents(state: CRAGState) -> dict:
        query = state.get("reformulated_query") or state["query"]
        results: list[GradeResult] = []
        for doc in state["retrieved_docs"]:
            grade: _DocGrade = grader.invoke([
                SystemMessage(content=(
                    "You are a relevance grader. Score how relevant the document chunk is to "
                    "answering the question. 0.0 = completely irrelevant, 1.0 = directly answers it."
                )),
                HumanMessage(content=f"Question: {query}\n\nDocument:\n{doc.page_content}"),
            ])
            results.append(GradeResult(
                doc_id=doc.metadata.get("source", "unknown"),
                score=grade.score,
                relevant=grade.score >= RELEVANCE_THRESHOLD,
                reason=grade.reason,
            ))
        return {"grade_results": results}

    def route_after_grading(state: CRAGState) -> str:
        passing = [r for r in state["grade_results"] if r["score"] >= RELEVANCE_THRESHOLD]
        if passing:
            return "generate"
        if state["iteration_count"] < MAX_ITERATIONS:
            return "reformulate_query"
        return "not_found"

    def reformulate_query(state: CRAGState) -> dict:
        best_fail = max(state["grade_results"], key=lambda r: r["score"])
        response = reformulator.invoke([
            SystemMessage(content=(
                "You are a query reformulator. The user's question failed to retrieve relevant documents. "
                "Rewrite it using different terminology that may better match the document content. "
                "Return only the reformulated question."
            )),
            HumanMessage(content=(
                f"Original question: {state['query']}\n"
                f"Closest match reason: {best_fail['reason']}\n"
                "Reformulated question:"
            )),
        ])
        return {
            "reformulated_query": response.content.strip(),
            "iteration_count": state["iteration_count"] + 1,
        }

    def generate(state: CRAGState) -> dict:
        passing = [
            (doc, grade)
            for doc, grade in zip(state["retrieved_docs"], state["grade_results"])
            if grade["score"] >= RELEVANCE_THRESHOLD
        ]
        context = "\n\n---\n\n".join(
            f"[{doc.metadata.get('source', '?')} · p.{doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc, _ in passing
        )
        query = state.get("reformulated_query") or state["query"]
        response = generator.invoke([
            SystemMessage(content=(
                "Answer the user's question using only the provided document excerpts. "
                "Cite sources by filename and page number. Be concise and accurate."
            )),
            HumanMessage(content=f"Question: {query}\n\nDocuments:\n{context}"),
        ])
        return {"final_answer": response.content}

    def not_found(state: CRAGState) -> dict:
        best = max(state["grade_results"], key=lambda r: r["score"], default=None)
        if best:
            msg = (
                f"I couldn't find relevant information in your documents. "
                f"(Best relevance score: {best['score']:.2f} — reason: '{best['reason']}')"
            )
        else:
            msg = "I couldn't find relevant information in your documents."
        return {"final_answer": msg}

    return {
        "retrieve": retrieve,
        "grade_documents": grade_documents,
        "route_after_grading": route_after_grading,
        "reformulate_query": reformulate_query,
        "generate": generate,
        "not_found": not_found,
    }
