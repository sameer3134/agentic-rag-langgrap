"""Streamlit entry point — RAG Assistant with per-user document isolation."""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

UPLOADS_DIR = Path("data/uploads")


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


@st.dialog("Welcome to RAG Assistant")
def _name_modal() -> None:
    st.write("Enter your name to create a personal document workspace.")
    name = st.text_input("Your name", placeholder="e.g. Alice")
    if st.button("Start", disabled=not name.strip(), use_container_width=True):
        st.session_state.user_name = name.strip()
        st.session_state.collection_name = f"crag_{_slugify(name.strip())}"
        st.rerun()


@st.cache_resource
def _load_graph(collection_name: str):
    from graph.graph import build_graph
    from observability import setup_observability
    setup_observability()
    return build_graph(collection_name)


def main() -> None:
    st.set_page_config(page_title="RAG Assistant", layout="wide")

    if "user_name" not in st.session_state:
        _name_modal()
        st.stop()

    user_name: str = st.session_state.user_name
    collection_name: str = st.session_state.collection_name
    graph = _load_graph(collection_name)

    st.title("RAG Assistant")
    st.caption(f"Workspace: **{user_name}** · collection `{collection_name}`")

    # PDF upload
    st.subheader("Upload Documents")
    uploaded = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    if uploaded:
        from ingest import ingest_pdfs
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        paths = []
        for f in uploaded:
            dest = UPLOADS_DIR / f.name
            dest.write_bytes(f.read())
            paths.append(dest)
        result = ingest_pdfs(paths, collection_name)
        for p in result.ingested:
            st.success(f"Ingested: {p.name}")
        for p in result.skipped:
            st.warning(f"Already in workspace: {p.name}")
        for p, reason in result.failed:
            st.error(f"Failed {p.name}: {reason}")

    st.divider()

    # Query
    st.subheader("Ask a Question")
    query = st.chat_input("Ask something about your documents...")
    if query:
        with st.spinner("Searching your documents..."):
            state = graph.invoke({
                "query": query,
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
                "user_id": user_name,
            })
        st.markdown(state["final_answer"] or "_No answer found._")

        with st.expander("Debug", expanded=False):
            for i, (doc, grade) in enumerate(
                zip(state.get("retrieved_docs", []), state.get("grade_results", []))
            ):
                badge = ":green[PASS]" if grade["relevant"] else ":red[FAIL]"
                st.markdown(
                    f"**Doc {i + 1}** {badge} · score `{grade['score']:.2f}` · "
                    f"`{doc.metadata.get('source', '?')}` p.{doc.metadata.get('page', '?')}\n\n"
                    f"_{grade['reason']}_"
                )
            if state.get("reformulated_query"):
                st.info(f"Reformulated query: {state['reformulated_query']}")
            st.caption(f"Iterations used: {state.get('iteration_count', 0)}")


if __name__ == "__main__":
    main()
