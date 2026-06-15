"""
LangGraph state schema for the agentic CRAG pipeline.

GradeResult and CRAGState are TypedDicts — intentionally simple dicts
with type annotations. LangGraph merges partial dicts between nodes;
mutable Pydantic models would break that merge contract.
"""
from typing import Optional, TypedDict


class GradeResult(TypedDict):
    """Relevance grade produced by the grade_documents node for one document."""

    doc_id: str
    score: float       # 0.0 – 1.0; threshold >= 0.7 passes
    relevant: bool     # score >= 0.7
    reason: str        # LLM explanation; surfaced in not_found response and Phoenix spans


class CRAGState(TypedDict):
    """
    Shared mutable state threaded through every LangGraph node.

    Immutability contract: each node returns a *partial dict* that
    LangGraph merges into the state — nodes must not mutate the input
    state dict in place.
    """

    query: str                           # Original user query — never overwritten
    reformulated_query: Optional[str]    # Set by reformulate_query node; None on first pass
    retrieved_docs: list                 # list[Document] — bare list avoids import-time LangChain dep
    grade_results: list                  # list[GradeResult] — populated by grade_documents node
    final_answer: Optional[str]          # Set by generate or not_found node
    iteration_count: int                 # Starts at 0; incremented by reformulate_query
    user_id: str                         # Display name of the user; used for tracing/debugging
