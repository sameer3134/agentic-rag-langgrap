"""LangGraph graph assembly and compilation for the CRAG pipeline."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from graph.state import CRAGState
from graph.nodes import (
    retrieve,
    grade_documents,
    reformulate_query,
    generate,
    not_found,
    route_after_grading,
)


def build_graph() -> Any:  # -> CompiledGraph (not exported as a public symbol in langgraph 0.2.x)
    """
    Assemble and compile the CRAG LangGraph state machine.

    Graph topology:
        retrieve → grade_documents
        grade_documents --[route_after_grading]--> generate | reformulate_query | not_found
        reformulate_query → retrieve  (loop)
        generate → END
        not_found → END

    Returns:
        A compiled LangGraph graph ready for .invoke() calls.
    """
    builder = StateGraph(CRAGState)

    # Register nodes
    builder.add_node("retrieve", retrieve)
    builder.add_node("grade_documents", grade_documents)
    builder.add_node("reformulate_query", reformulate_query)
    builder.add_node("generate", generate)
    builder.add_node("not_found", not_found)

    # Entry point
    builder.set_entry_point("retrieve")

    # Fixed edges
    builder.add_edge("retrieve", "grade_documents")
    builder.add_edge("reformulate_query", "retrieve")
    builder.add_edge("generate", END)
    builder.add_edge("not_found", END)

    # Conditional edge
    builder.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "generate": "generate",
            "reformulate_query": "reformulate_query",
            "not_found": "not_found",
        },
    )

    return builder.compile()
