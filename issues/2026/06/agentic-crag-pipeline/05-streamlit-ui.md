# feat: Streamlit UI for ingestion and querying

> Issue #5 | Branch `feat/streamlit-ui` | Type AFK
> Depends on: #2, #3, #4
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Implement `app.py` — the Streamlit application that ties every prior slice together. The app has two functional areas: a PDF upload section that drives the ingestion pipeline, and a query section that invokes the CRAG graph and renders the answer plus a collapsible debug panel. Phoenix observability is initialized once at startup. The app runs locally with `streamlit run app.py`, requires no authentication, and is the complete user-facing interface for the project.

## Resolved decisions

**App startup sequence:**
1. `load_dotenv()` to populate env vars
2. `setup_observability()` from `observability.py` — launches Phoenix, registers instrumentor
3. Initialize (or load existing) Chroma vector store
4. Compile CRAG graph via `build_graph()` from `graph/graph.py`

All four steps run once via `@st.cache_resource` to survive Streamlit reruns.

**PDF upload section:**
- `st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)`
- On upload: save each file to `data/uploads/{filename}`, call `ingest_pdfs([...paths])`, display `IngestResult` as three colored status lists:
  - Green: ingested filenames
  - Yellow: skipped (already in knowledge base)
  - Red: failed with reason

**Query section:**
- `st.text_input` or `st.chat_input` for the user's question
- On submit: display `st.spinner("Thinking...")` while the graph runs
- Invoke graph with initial state: `{"query": user_query, "reformulated_query": None, "retrieved_docs": [], "grade_results": [], "final_answer": None, "iteration_count": 0}`
- Display `final_answer` in a prominent `st.markdown` block (top of response area)

**Debug / Trace panel** (collapsible `st.expander("Debug / Trace", expanded=False)`):
- **Retrieved documents:** for each doc in `state["retrieved_docs"]`, show the chunk source filename, page number, and the matching `GradeResult.score` + `GradeResult.reason`. Color-code: green if `score >= 0.7`, red if below.
- **Reformulation history:** if `reformulated_query` is not None, show `"Original: {query}"` → `"Reformulated: {reformulated_query}"`. If `iteration_count > 1`, show all reformulation steps (store intermediate queries in state or surface from grade loop).
- **Iteration count:** `"Iterations: {iteration_count}"`

**Phoenix link:** Display `st.caption("Phoenix traces: http://localhost:{PHOENIX_PORT}")` in the sidebar so the user can click through to the trace UI.

**No authentication:** Local-only app, no login, no session isolation.

**File persistence:** Uploaded PDFs saved to `data/uploads/` before ingestion so they survive app restarts.

**Error display:** If the graph raises an unhandled exception, catch it and display `st.error(str(e))` rather than crashing the app.

## Acceptance criteria

- [ ] `streamlit run app.py` starts without error and opens in the browser
- [ ] Phoenix UI link appears in the sidebar pointing to the correct port
- [ ] Uploading a valid PDF shows the filename in the green "ingested" list
- [ ] Re-uploading the same PDF shows the filename in the yellow "skipped" list
- [ ] Uploading a corrupted PDF shows the filename in the red "failed" list; other files in the same batch are still ingested
- [ ] Submitting a query displays a spinner while the graph runs
- [ ] The final answer appears prominently above the debug panel
- [ ] The debug panel is collapsed by default and expands on click
- [ ] The debug panel shows each retrieved chunk's source, page, score, and reason
- [ ] Passing chunks (score ≥ 0.7) are visually distinguished from failing chunks in the debug panel
- [ ] When reformulation occurred, the debug panel shows both the original and reformulated query
- [ ] When no relevant documents are found, the "not found" message (including best score and reason) is displayed as the final answer

## Out of scope

- Multi-turn chat history — each query is stateless
- Authentication or user accounts
- Cloud deployment — local `streamlit run` only
- Any UI for triggering `eval.py` — that remains a CLI script (issue #6)
