"""LangGraph graph assembly — build_graph(collection_name) returns a compiled CRAG graph."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from graph.nodes import make_nodes
from graph.state import CRAGState


def build_graph(collection_name: str):
    """Compile and return a CRAG graph scoped to the given Chroma collection."""
    nodes = make_nodes(collection_name)

    builder = StateGraph(CRAGState)
    builder.add_node("retrieve", nodes["retrieve"])
    builder.add_node("grade_documents", nodes["grade_documents"])
    builder.add_node("reformulate_query", nodes["reformulate_query"])
    builder.add_node("generate", nodes["generate"])
    builder.add_node("not_found", nodes["not_found"])

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "grade_documents")
    builder.add_conditional_edges(
        "grade_documents",
        nodes["route_after_grading"],
        {"generate": "generate", "reformulate_query": "reformulate_query", "not_found": "not_found"},
    )
    builder.add_edge("reformulate_query", "retrieve")
    builder.add_edge("generate", END)
    builder.add_edge("not_found", END)

    return builder.compile()
