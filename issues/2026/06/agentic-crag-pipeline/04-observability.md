# feat: Arize Phoenix observability setup

> Issue #4 | Branch `feat/observability` | Type AFK
> Depends on: #3
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Implement `observability.py` — a single `setup_observability()` function that launches Arize Phoenix in-process and registers the LangChain auto-instrumentor. Called once at Streamlit app startup. After this slice, every LangGraph node execution, LLM call, and retriever call is automatically captured as a named OpenTelemetry span visible in the Phoenix UI at `http://localhost:{PHOENIX_PORT}`.

## Resolved decisions

**Deployment mode:** Local in-process — `px.launch_app()`. No Docker, no cloud Phoenix. Phoenix UI served on `PHOENIX_PORT` (default `6006`).

**Trace persistence:** Traces written to `PHOENIX_TRACE_DIR` (default `./phoenix_traces`). Set via `os.environ["PHOENIX_WORKING_DIR"] = PHOENIX_TRACE_DIR` before calling `px.launch_app()`.

**Instrumentation:** `openinference-instrumentation-langchain` auto-instrumentor:
```python
from openinference.instrumentation.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument()
```
This automatically captures:
- Every LLM call (grader `gpt-4o-mini`, generator `gpt-4o`) as an `LLM` span
- Every Chroma retriever call as a `RETRIEVER` span
- Every LangGraph node execution as a named `CHAIN` span

**Span attributes for grade results:** After `grade_documents` runs, `GradeResult.score` and `GradeResult.reason` are already present in the LangGraph state — the auto-instrumentor will capture the structured output payload from the LLM call. No manual span attribute setting is required.

**Public interface:**
```python
def setup_observability() -> None:
    """Launch Phoenix in-process and register LangChain instrumentor. Idempotent."""
```

**Idempotency:** Guard against double-initialization (Streamlit reruns `app.py` on every interaction). Use a module-level `_initialized` flag or check `px.active_session()` before calling `launch_app()`.

**Environment variables consumed:**
- `PHOENIX_PORT` — Phoenix UI port, default `6006`
- `PHOENIX_TRACE_DIR` — trace storage directory, default `./phoenix_traces`

## Acceptance criteria

- [ ] `setup_observability()` can be called twice without raising or launching a second Phoenix instance
- [ ] After `setup_observability()` is called, `px.active_session()` returns a non-None session object
- [ ] Phoenix UI is accessible at `http://localhost:{PHOENIX_PORT}` after setup
- [ ] Invoking the compiled CRAG graph (from #3) after setup produces at least one trace in the Phoenix UI containing named spans for LangGraph nodes
- [ ] `PHOENIX_TRACE_DIR` directory is created if it does not exist
- [ ] `PHOENIX_PORT` env var overrides the default port 6006

## Out of scope

- Manual span creation or attribute injection beyond what the auto-instrumentor captures
- Cloud Phoenix (app.phoenix.arize.com) — local in-process only
- Streamlit UI integration — `setup_observability()` is called from `app.py` in issue #5
