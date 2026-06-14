"""Streamlit application — PDF ingestion and CRAG querying UI.

Run with: streamlit run app.py

Startup sequence (once per server process, cached):
  1. load_dotenv()
  2. setup_observability()  — launches Phoenix, registers LangChain instrumentor
  3. Chroma vectorstore     — connects to existing crag_corpus collection
  4. build_graph()          — compiles the CRAG LangGraph state machine
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from graph.graph import build_graph
from ingest import ingest_pdfs
from observability import setup_observability


@st.cache_resource
def _init_resources():
    """Run once per Streamlit server process. Returns (vectorstore, compiled_graph)."""
    load_dotenv()
    setup_observability()

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="crag_corpus",
        embedding_function=embeddings,
        persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
    )
    graph = build_graph()
    return vectorstore, graph


def _render_debug_panel(state: dict) -> None:
    """Render the collapsible Debug / Trace expander."""
    with st.expander("Debug / Trace", expanded=False):
        st.subheader("Retrieved Documents")
        retrieved_docs = state.get("retrieved_docs", [])
        grade_results = state.get("grade_results", [])
        if not retrieved_docs:
            st.write("No documents retrieved.")
        for doc, grade in zip(retrieved_docs, grade_results):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "?")
            score = grade["score"]
            reason = grade["reason"]
            label = f"`{source}` — page {page} — score {score:.2f}"
            if score >= 0.7:
                st.success(f"{label}\n\nReason: {reason}")
            else:
                st.error(f"{label}\n\nReason: {reason}")

        st.subheader("Reformulation History")
        if state.get("reformulated_query") is not None:
            st.write(f"Original: {state['query']}")
            st.write(f"Reformulated: {state['reformulated_query']}")
        else:
            st.write("No reformulation was triggered.")

        st.subheader("Iterations")
        st.write(f"Iterations: {state.get('iteration_count', 0)}")


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CRAG Pipeline", layout="wide")
st.title("Agentic CRAG Pipeline")

# Sidebar — Phoenix link
phoenix_port = int(os.getenv("PHOENIX_PORT", "6006"))
st.sidebar.caption(f"Phoenix traces: http://localhost:{phoenix_port}")

# Initialise all resources (cached after first run)
_vectorstore, graph = _init_resources()

# ---------------------------------------------------------------------------
# PDF Upload section
# ---------------------------------------------------------------------------

st.header("PDF Ingestion")

Path("data/uploads").mkdir(parents=True, exist_ok=True)

uploaded_files = st.file_uploader(
    "Upload PDFs", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    if st.button("Ingest"):
        saved_paths: list[Path] = []
        for uf in uploaded_files:
            dest = Path("data/uploads") / uf.name
            dest.write_bytes(uf.getvalue())
            saved_paths.append(dest)

        with st.spinner("Ingesting..."):
            result = ingest_pdfs(saved_paths)

        if result.ingested:
            st.success(f"Ingested: {', '.join(result.ingested)}")
        if result.skipped:
            st.warning(
                f"Skipped (already in knowledge base): {', '.join(result.skipped)}"
            )
        if result.failed:
            for entry in result.failed:
                st.error(f"Failed: {entry}")

# ---------------------------------------------------------------------------
# Query section
# ---------------------------------------------------------------------------

st.header("Query")

user_query = st.chat_input("Ask a question about your documents...")

if user_query:
    try:
        with st.spinner("Thinking..."):
            state = graph.invoke(
                {
                    "query": user_query,
                    "reformulated_query": None,
                    "retrieved_docs": [],
                    "grade_results": [],
                    "final_answer": None,
                    "iteration_count": 0,
                }
            )
        st.markdown(state["final_answer"])
        _render_debug_panel(state)
    except Exception as e:
        st.error(str(e))
