# PR5 — feat: Streamlit UI for ingestion and querying

**Branch:** `feat/streamlit-ui`
**PR ID:** PR-5
**Depends on:** PR-2 (feat/pdf-ingestion), PR-3 (feat/crag-graph), PR-4 (feat/observability)

---

## What This PR Does

This PR replaces the three-line `app.py` stub with the complete Streamlit application that ties every prior slice together. It implements a PDF upload section (drag-and-drop multi-file upload → `ingest_pdfs()` → colour-coded `IngestResult` display) and a query section (`st.chat_input` → CRAG graph → final answer + collapsible debug/trace panel). Arize Phoenix observability is initialised once at startup via `@st.cache_resource`, and a sidebar link to the Phoenix UI is displayed throughout the session. The app is the single user-facing interface for the project; all logic it calls was already tested in prior PRs, so this PR adds only presentation-layer code and a test for the app's error-handling path.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | `st.chat_input` vs `st.text_input` for query entry | `st.chat_input` | Issue spec says `st.text_input` or `st.chat_input`; `st.chat_input` is the idiomatic choice for Streamlit 1.38.x query UX and is available since 1.31 | If Streamlit version is pinned below 1.31 |
| 2 | Cache decorator for startup resources | `@st.cache_resource` wrapping a single `_init_resources()` function that returns `(vectorstore, graph)` | Issue spec mandates `@st.cache_resource` for all four startup steps; grouping them in one cached function is the simplest pattern that survives reruns | If the vectorstore or graph needs to be refreshed mid-session |
| 3 | `data/uploads/` directory creation | `Path("data/uploads").mkdir(parents=True, exist_ok=True)` called at the top of the upload handler, not at module load | Avoids creating the directory when the app starts in a read-only filesystem; matches `os.makedirs(exist_ok=True)` convention in `observability.py` | Never — defensive is correct |
| 4 | Error display strategy for graph exceptions | `st.error(str(e))` inside a bare `except Exception as e` block, followed by `st.stop()` | Issue spec explicitly specifies `st.error(str(e))`; `st.stop()` prevents blank output below the error message | If structured error codes are introduced |
| 5 | `IngestResult.failed` list format | Each entry is `"filename: reason"` (colon-separated) as produced by `ingest.py`; split on first `: ` to display filename vs. reason separately in the UI | `ingest.py` builds entries as `f"{file_path.name}: {reason}"` (line 149); the app must not assume a different format | If `ingest.py` changes its failed-entry format |
| 6 | Reformulation history in state | Surface only the most recent `reformulated_query` from `CRAGState`; the issue spec says "show `'Original: {query}' → 'Reformulated: {reformulated_query}'`" and notes intermediate queries "or surface from grade loop" — the `CRAGState` schema (from PR-3) stores only the latest `reformulated_query`, not a list, so only one reformulation step can be shown | If `CRAGState` is extended to store a list of reformulations |
| 7 | `PHOENIX_PORT` read in `app.py` | `int(os.getenv("PHOENIX_PORT", "6006"))` — read from env, not imported from `observability.py` | `observability.py` does not export the port it used; re-reading from env is the correct approach since the env var is the source of truth | Never |
| 8 | Test coverage for `app.py` | One smoke-test: `test_app_error_display` patches `build_graph` to raise and verifies `st.error` is called; no full Streamlit integration test | Streamlit apps are hard to integration-test without `streamlit.testing.v1.AppTest` which requires Streamlit 1.28+; the app's logic is fully tested in prior PRs; this single test guards the error-handling path | If AppTest integration tests are added separately |
| 9 | `@st.cache_resource` vs `@st.cache_data` | `@st.cache_resource` for the startup initialiser | `st.cache_resource` is the correct decorator for stateful objects (Chroma vectorstore, compiled graph) that must not be pickled; `st.cache_data` serialises its return value | Never — PRD and issue spec are explicit |
| 10 | Upload temp file persistence | Save uploaded files to `data/uploads/{original_filename}` before calling `ingest_pdfs` | Issue spec §File persistence requires this; `st.file_uploader` returns an in-memory `UploadedFile` object that does not survive reruns | Never — issue spec is explicit |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | `_init_resources()` cached startup function: `load_dotenv`, `setup_observability`, Chroma init, `build_graph` | `app.py` |
| T2 | PDF upload section: file uploader, save to disk, call `ingest_pdfs`, colour-coded result display | `app.py` |
| T3 | Query section: `st.chat_input`, spinner, graph invoke with initial state, final answer display | `app.py` |
| T4 | Debug / Trace expander: retrieved docs with grade colour-coding, reformulation history, iteration count | `app.py` |
| T5 | Sidebar Phoenix link | `app.py` |
| T6 | Unhandled exception guard | `app.py` |
| T7 | Unit test: `test_app_error_display` — graph exception triggers `st.error` | `tests/test_app.py` |

---

## Architecture Constraints

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| `app.py` is purely a presentation layer — no business logic, no LLM calls, no Chroma queries directly | PRD §Dependencies & Sequencing step 6 | Any business logic in `app.py` would bypass the tested modules and introduce untested code paths |
| All four startup steps must run inside a single `@st.cache_resource` function | Issue spec §App startup sequence | Running them outside the cache means they re-execute on every Streamlit rerun, causing duplicate Phoenix instances and multiple graph compiles |
| `setup_observability()` must be called before `build_graph()` | PRD §Observability | The `LangChainInstrumentor` must be registered before the graph is compiled so that node spans are captured; calling it after compilation misses some hooks on certain `openinference` versions |
| Uploaded PDFs must be saved to `data/uploads/{filename}` before `ingest_pdfs` is called | Issue spec §File persistence | `ingest_pdfs` accepts `list[Path]` — it reads from disk; passing an in-memory `UploadedFile` directly raises `TypeError` |
| Initial CRAG graph state must include all six `CRAGState` keys | `graph/state.py` `CRAGState` TypedDict | Missing keys cause `KeyError` inside node functions that access them with `state["key"]` rather than `state.get("key")` |
| Graph invocation must use `.invoke()` not `.stream()` | Issue spec §Query section | The issue spec calls for a single blocking call and full-state result; `.stream()` returns an iterator of partial states that requires different rendering logic |
| `final_answer` must be displayed with `st.markdown` | Issue spec §Query section | `st.write` would not render markdown formatting in the generated answer; `st.markdown` is explicitly required |
| Debug panel must use `st.expander` with `expanded=False` | Issue spec §Debug / Trace panel | Default-expanded debug panel violates the acceptance criterion "collapsed by default" |
| Score colour threshold: `score >= 0.7` is green, below is red | Issue spec §Debug / Trace panel | Threshold must match `GRADE_THRESHOLD = 0.7` in `graph/nodes.py`; a different threshold creates a confusing mismatch between the UI colour and actual routing behaviour |
| `st.error(str(e))` for unhandled graph exceptions | Issue spec §Error display | Letting the exception propagate crashes the Streamlit process and leaves the user with a blank screen |
| No authentication, no session isolation | Issue spec §No authentication | App is local-only; adding auth would contradict the scope constraint |
| Unit tests must not require `OPENAI_API_KEY` or a live Phoenix server | Established convention (all prior test files) | CI without API key would break |

---

## T1 — `_init_resources()` Startup Cached Function

### What it builds

A `@st.cache_resource`-decorated function that runs the four startup steps exactly once per Streamlit server process: `load_dotenv()`, `setup_observability()`, Chroma vectorstore initialisation (shared with `ingest.py`), and `build_graph()`. Returns `(vectorstore, graph)` so the rest of the app can reference them without re-importing from sub-modules.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Return value | `tuple[Chroma, CompiledGraph]` | Both are stateful objects that must be shared across reruns via the cache |
| Chroma init in `app.py` | Call `Chroma(collection_name="crag_corpus", embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"), persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))` directly | `ingest.py` exposes `_get_vectorstore()` but it is prefixed with `_` (private); the correct approach is to construct the vectorstore with the same parameters rather than calling a private function |
| `load_dotenv()` placement | Inside `_init_resources()` before any env reads | `@st.cache_resource` runs the function body only once; calling `load_dotenv()` there is sufficient and avoids a module-level side effect |

### Layer compliance checklist

- [ ] No LLM calls in `_init_resources()` — only client/session initialisation
- [ ] `setup_observability()` called before `build_graph()`
- [ ] `@st.cache_resource` applied — not `@st.cache_data`

### Full implementation

```python
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from observability import setup_observability
from graph.graph import build_graph


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
```

### Verifiable acceptance criteria

- [ ] Calling `_init_resources()` twice (simulating a rerun) returns the same objects (same `id()`)
- [ ] `setup_observability` is called before `build_graph` in the function body (verified by inspection)

---

## T2 — PDF Upload Section

### What it builds

The left column (or top section) of the app: a `st.file_uploader` that accepts multiple PDFs, saves each to `data/uploads/`, calls `ingest_pdfs()`, and renders `IngestResult` as three labelled lists — green (ingested), yellow (skipped), red (failed).

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Upload directory | `Path("data/uploads")` | Issue spec §File persistence mandates this path |
| File saving | `target = Path("data/uploads") / uploaded_file.name; target.write_bytes(uploaded_file.getvalue())` | `st.UploadedFile.getvalue()` returns raw bytes; `Path.write_bytes()` is the simplest write |
| Result colour rendering | `st.success` for ingested, `st.warning` for skipped, `st.error` for failed | Streamlit's semantic status functions map naturally to green/yellow/red without custom CSS |
| Trigger condition | `if uploaded_files:` — render button only when files are staged | Avoids confusing "Ingest" button when no files are uploaded |

### Full implementation

```python
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
            from ingest import ingest_pdfs
            result = ingest_pdfs(saved_paths)

        if result.ingested:
            st.success(f"Ingested: {', '.join(result.ingested)}")
        if result.skipped:
            st.warning(f"Skipped (already in knowledge base): {', '.join(result.skipped)}")
        if result.failed:
            for entry in result.failed:
                st.error(f"Failed: {entry}")
```

### Verifiable acceptance criteria

- [ ] Uploading a valid PDF shows the filename in a green `st.success` element
- [ ] Re-uploading the same PDF shows the filename in a yellow `st.warning` element
- [ ] Uploading a corrupted PDF shows the entry in a red `st.error` element; other files in the same batch still appear in `st.success`

---

## T3 — Query Section

### What it builds

A `st.chat_input` that accepts a user question, shows `st.spinner("Thinking...")` while the graph runs, invokes the graph with the canonical initial `CRAGState`, and renders `final_answer` via `st.markdown`.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Input widget | `st.chat_input("Ask a question about your documents...")` | Idiomatic for 1.38.x; renders at the bottom of the page; submit on Enter |
| Initial state dict | All six `CRAGState` keys with zero values | `CRAGState` is a TypedDict; missing keys cause `KeyError` in node functions |
| Graph reference | Retrieved from `_init_resources()` return value | Avoids re-importing `build_graph` and recompiling the graph on every rerun |

### Full implementation

```python
st.header("Query")

_vectorstore, graph = _init_resources()

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
            })
        st.markdown(state["final_answer"])
        _render_debug_panel(state)
    except Exception as e:
        st.error(str(e))
```

### Verifiable acceptance criteria

- [ ] Submitting a query displays `st.spinner` while the graph runs
- [ ] `final_answer` is rendered with `st.markdown` above the debug panel
- [ ] A graph exception displays `st.error(str(e))` and does not crash the app

---

## T4 — Debug / Trace Expander

### What it builds

A `st.expander("Debug / Trace", expanded=False)` containing: retrieved documents with grade colour-coding, reformulation history, and iteration count.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Grade colour | `st.success` if `score >= 0.7`, else `st.error` | Mirrors the `GRADE_THRESHOLD = 0.7` constant in `nodes.py`; consistent visual language with the upload result display |
| Doc metadata rendering | `doc.metadata.get("source", "unknown")` and `doc.metadata.get("page", "?")` | `_chunk_pdf` in `ingest.py` stores `source` and `page` in metadata; `.get()` with defaults handles legacy chunks without these fields |
| Reformulation display | Show only when `state["reformulated_query"] is not None` | `CRAGState` schema stores only the latest reformulated query; no list of intermediates is available without schema change |
| `grade_results` / `retrieved_docs` alignment | Zip `state["retrieved_docs"]` with `state["grade_results"]` | `grade_documents` node produces one `GradeResult` per retrieved doc in order; zip is the correct alignment strategy |

### Full implementation

```python
def _render_debug_panel(state: dict) -> None:
    with st.expander("Debug / Trace", expanded=False):
        st.subheader("Retrieved Documents")
        retrieved_docs = state.get("retrieved_docs", [])
        grade_results = state.get("grade_results", [])
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
```

### Verifiable acceptance criteria

- [ ] Debug panel is collapsed by default
- [ ] Each chunk shows source filename, page number, score, and reason
- [ ] Chunks with `score >= 0.7` rendered in green (`st.success`)
- [ ] Chunks with `score < 0.7` rendered in red (`st.error`)
- [ ] When `reformulated_query` is not None, both original and reformulated queries are shown
- [ ] Iteration count is displayed

---

## T5 — Sidebar Phoenix Link

### What it builds

A `st.sidebar.caption` that displays the Phoenix UI URL using the configured port.

### Full implementation

```python
phoenix_port = int(os.getenv("PHOENIX_PORT", "6006"))
st.sidebar.caption(f"Phoenix traces: http://localhost:{phoenix_port}")
```

### Verifiable acceptance criteria

- [ ] Phoenix link appears in sidebar on app load
- [ ] Link reflects `PHOENIX_PORT` env var when overridden (e.g., port 6007 shows `http://localhost:6007`)

---

## T6 — Unhandled Exception Guard

Already covered in T3's `try/except Exception as e: st.error(str(e))` block around the graph invocation. The entire query section is wrapped so any exception from any part of the pipeline (graph, LLM call, retriever) is caught.

### Verifiable acceptance criteria

- [ ] If `graph.invoke()` raises any `Exception`, `st.error(str(e))` is called
- [ ] App does not crash (Streamlit process continues serving)

---

## T7 — Unit Test: `tests/test_app.py`

### What it builds

A single test module that guards the error-handling path of `app.py`. Uses `unittest.mock` to patch `build_graph`, `setup_observability`, and `OpenAIEmbeddings`/`Chroma` so no real services are needed. Uses `streamlit.testing.v1.AppTest` (available in Streamlit 1.38.x) to run the app in a test context.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Test runner | `streamlit.testing.v1.AppTest` | Available since Streamlit 1.28; the correct way to test Streamlit apps without a live server |
| Mock scope | Patch `graph.graph.build_graph`, `observability.setup_observability`, `langchain_openai.OpenAIEmbeddings`, `langchain_community.vectorstores.Chroma` | Prevents real API calls and Phoenix launch in tests |
| Test case count | 1 (error display) | The app's upload and query logic delegates to `ingest_pdfs` and `graph.invoke`, both tested in prior PRs; only the error-handling path is exclusive to `app.py` |

### Full implementation

```python
"""Unit tests for app.py.

Run with: pytest tests/test_app.py -v
No OPENAI_API_KEY or live Phoenix server required.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestAppErrorHandling:
    def test_graph_exception_displays_st_error(self, tmp_path, monkeypatch):
        """If the CRAG graph raises, app.py must call st.error and not crash."""
        monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
        monkeypatch.setenv("PHOENIX_PORT", "6006")
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        # Provide a dummy API key so langchain_openai imports don't fail
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = RuntimeError("LLM call failed")

        mock_vectorstore = MagicMock()

        with patch("graph.graph.build_graph", return_value=mock_graph), \
             patch("observability.setup_observability"), \
             patch("langchain_openai.OpenAIEmbeddings", return_value=MagicMock()), \
             patch("langchain_community.vectorstores.Chroma", return_value=mock_vectorstore):
            from streamlit.testing.v1 import AppTest
            at = AppTest.from_file("app.py", default_timeout=10)
            at.run()
            # Simulate user submitting a query
            at.chat_input[0].set_value("What is CRAG?").run()

        # st.error should be called with the exception message
        assert any("LLM call failed" in str(e.value) for e in at.error)
```

### Verifiable acceptance criteria

- [ ] `pytest tests/test_app.py -v` passes without `OPENAI_API_KEY`
- [ ] No real Phoenix server started during test

---

## Full `app.py` Implementation

```python
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
```

---

## Migration

Not applicable — this PR adds no database models, migrations, or schema changes. `app.py` is a presentation-layer module with no persistent data layer.

---

## Test quality rules

- **`@st.cache_resource` behaviour:** verify idempotency by calling `_init_resources()` twice in a mocked context and asserting `build_graph` was called only once — not just that no exception was raised.
- **State dict completeness:** any test that invokes the graph must supply all six `CRAGState` keys; assert on the keys present in the initial state dict, not just the final answer.
- **Upload file format:** use `io.BytesIO` or a minimal valid PDF (as produced by `_build_pdf` in `test_ingest.py`) when constructing mock `UploadedFile` objects — not empty bytes, which would trigger `ingest.py`'s parse-failure path.
- **`OPENAI_API_KEY` isolation:** use `monkeypatch.setenv("OPENAI_API_KEY", "test-key")` — do not read from the real environment; the key is syntactically required by `langchain_openai` constructors even when mocked.
- **`st.cache_resource` test isolation:** call `st.cache_resource.clear()` (or use `AppTest` which isolates cache) between test cases that call `_init_resources()` to avoid cross-test contamination.

---

## Automated verification

```bash
pytest tests/test_app.py -v
pytest tests/ -v
streamlit run app.py --server.headless true &
```

---

## Manual verification

1. **App starts without error:**
   - Ensure `.env` is configured with a valid `OPENAI_API_KEY`
   - Run `streamlit run app.py`
   - Expected: browser opens at `http://localhost:8501`, no red error banner on startup

2. **Phoenix sidebar link:**
   - After app starts, inspect the sidebar
   - Expected: `Phoenix traces: http://localhost:6006` (or configured port) appears as a caption

3. **PDF upload — ingestion:**
   - Upload any valid PDF via the file uploader and click Ingest
   - Expected: green `st.success` message with the filename appears

4. **PDF upload — dedup:**
   - Upload the same PDF a second time and click Ingest
   - Expected: yellow `st.warning` "Skipped (already in knowledge base)" message

5. **PDF upload — corrupted file:**
   - Rename a `.txt` file to `.pdf` and upload it
   - Expected: red `st.error` "Failed: ..." message; other files in the same batch are still ingested

6. **Query — spinner:**
   - Type a question in the chat input and press Enter
   - Expected: `st.spinner("Thinking...")` appears while the graph runs

7. **Query — final answer above debug panel:**
   - After the graph completes, verify the answer text appears above the "Debug / Trace" expander

8. **Debug panel — collapsed by default:**
   - Expected: expander is collapsed; clicking it reveals the retrieved documents section

9. **Debug panel — grade colour coding:**
   - Expected: chunks with score >= 0.7 appear in green (`st.success`); chunks below 0.7 appear in red (`st.error`)

10. **Debug panel — reformulation:**
    - Ask a very obscure question that forces reformulation (e.g., a question with unusual phrasing not matching any chunk)
    - Expected: "Reformulation History" shows both original and reformulated query

11. **Error handling:**
    - Temporarily set `OPENAI_API_KEY=invalid` in `.env`; ask a question
    - Expected: `st.error` message appears with the API error text; app does not crash

12. **Not-found response:**
    - Ask a question completely unrelated to the uploaded PDFs
    - Expected: final answer starts with "I couldn't find relevant information in the knowledge base." and includes a best relevance score and reason

---

## Implementation Notes

### T7 — `pandas` / `phoenix` import error in test environment

**Observed:** `arize-phoenix 4.36.0` imports `pandas` at module level via `phoenix.inferences.fixtures`. `pandas` was not installed in the test environment, causing `ModuleNotFoundError` when `patch("observability.setup_observability")` triggered the `observability.py` module import (which does `import phoenix as px` at module level).

**Resolution:** Added `monkeypatch.setitem(sys.modules, "phoenix", MagicMock())` and stubs for `phoenix.inferences`, `phoenix.inferences.fixtures`, `openinference.instrumentation`, and `openinference.instrumentation.langchain` before the `with patch(...)` block. This prevents the real `phoenix` package from being imported during tests. `pandas` was also installed as a side effect of installing `streamlit==1.38.0` (which depends on it), so subsequent runs will not hit this error; the stub remains as defensive isolation.

**CLAUDE.md conflict:** None — the convention "unit tests must not require live Phoenix server" is satisfied.

### T1–T6 — Streamlit not installed

**Observed:** `streamlit` was absent from the environment (`pip list` returned nothing). The `requirements.txt` specifies `streamlit==1.38.*` but it had not been installed.

**Resolution:** Ran `pip install 'streamlit==1.38.*'`. `streamlit==1.38.0` installed successfully. All 45 tests pass.
