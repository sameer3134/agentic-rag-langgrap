"""Streamlit application — CRAG pipeline with per-user document isolation.

Run with: streamlit run app.py

On first open a modal asks for the user's name, creating a personal
Chroma collection (crag_{slug}) that isolates their documents from
all other users.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from graph.graph import build_graph
from ingest import ingest_pdfs
from observability import setup_observability

# ---------------------------------------------------------------------------
# Config — must be first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CRAG Pipeline", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_secrets() -> None:
    """Load from .env (local) then st.secrets (Streamlit Cloud), without overwriting."""
    load_dotenv()
    for key in ("OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "PHOENIX_PORT"):
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = st.secrets[key]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


@st.dialog("Welcome to CRAG Pipeline")
def _name_modal() -> None:
    st.write("Enter your name to create a personal document workspace.")
    with st.form("name_form", border=False):
        name = st.text_input("Your name", placeholder="e.g. Alice")
        submitted = st.form_submit_button("Start", use_container_width=True)
    if submitted:
        if name.strip():
            st.session_state.user_name = name.strip()
            st.session_state.collection_name = f"crag_{_slugify(name.strip())}"
            st.query_params["user"] = name.strip()
            st.rerun()
        else:
            st.error("Please enter your name.")


@st.cache_resource
def _init_graph(collection_name: str):
    """Build and cache one compiled graph per user collection."""
    _load_secrets()
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set. Add it to .env or Streamlit Cloud secrets.")
        st.stop()
    setup_observability()
    return build_graph(collection_name)


def _render_debug_panel(state: dict) -> None:
    with st.expander("Debug / Trace", expanded=False):
        st.subheader("Retrieved Documents")
        retrieved_docs = state.get("retrieved_docs", [])
        grade_results = state.get("grade_results", [])
        if not retrieved_docs:
            st.write("No documents retrieved.")
        for doc, grade in zip(retrieved_docs, grade_results):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "?")
            label = f"`{source}` — page {page} — score {grade['score']:.2f}"
            if grade["score"] >= 0.7:
                st.success(f"{label}\n\nReason: {grade['reason']}")
            else:
                st.error(f"{label}\n\nReason: {grade['reason']}")

        st.subheader("Reformulation History")
        if state.get("reformulated_query"):
            st.write(f"Original: {state['query']}")
            st.write(f"Reformulated: {state['reformulated_query']}")
        else:
            st.write("No reformulation was triggered.")

        st.subheader("Iterations")
        st.write(f"Iterations used: {state.get('iteration_count', 0)}")


# ---------------------------------------------------------------------------
# Gate: restore from URL on refresh, show modal only on fresh visit
# ---------------------------------------------------------------------------

if "user_name" not in st.session_state:
    param_name = st.query_params.get("user", "").strip()
    if param_name:
        st.session_state.user_name = param_name
        st.session_state.collection_name = f"crag_{_slugify(param_name)}"

if "user_name" not in st.session_state:
    _name_modal()
    st.stop()

user_name: str = st.session_state.user_name
collection_name: str = st.session_state.collection_name
graph = _init_graph(collection_name)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.title("Agentic CRAG Pipeline")
st.caption(f"Workspace: **{user_name}** · collection `{collection_name}`")

phoenix_port = int(os.getenv("PHOENIX_PORT", "6006"))
st.sidebar.caption(f"Phoenix traces: http://localhost:{phoenix_port}")

if st.sidebar.button("Switch user", use_container_width=True):
    del st.session_state["user_name"]
    del st.session_state["collection_name"]
    st.query_params.clear()
    st.rerun()

# ---------------------------------------------------------------------------
# PDF Upload
# ---------------------------------------------------------------------------

st.header("PDF Ingestion")
Path("data/uploads").mkdir(parents=True, exist_ok=True)

uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Ingest"):
        saved_paths: list[Path] = []
        for uf in uploaded_files:
            dest = Path("data/uploads") / uf.name
            dest.write_bytes(uf.getvalue())
            saved_paths.append(dest)

        with st.spinner("Ingesting..."):
            result = ingest_pdfs(saved_paths, collection_name)

        if result.ingested:
            st.success(f"Ingested: {', '.join(result.ingested)}")
        if result.skipped:
            st.warning(f"Skipped (already in workspace): {', '.join(result.skipped)}")
        for entry in result.failed:
            st.error(f"Failed: {entry}")

# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

st.header("Query")

user_query = st.chat_input("Ask a question about your documents...")

if user_query:
    try:
        with st.spinner("Thinking..."):
            state = graph.invoke({
                "query": user_query,
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
                "user_id": user_name,
            })
        st.markdown(state["final_answer"])
        _render_debug_panel(state)
    except Exception as e:
        st.error(str(e))
