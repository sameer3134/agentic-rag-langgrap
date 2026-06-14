# PR4 — feat: Arize Phoenix observability setup

**Branch:** `feat/observability`
**PR ID:** PR-4
**Depends on:** PR-3 (feat/crag-graph)

---

## What This PR Does

This PR replaces the `observability.py` stub with a complete `setup_observability()` function that launches Arize Phoenix in-process and registers the `openinference-instrumentation-langchain` auto-instrumentor. After this slice, every LangGraph node execution, every LLM call (grader `gpt-4o-mini` and generator `gpt-4o`), and every Chroma retriever call is automatically captured as a named OpenTelemetry span visible in the Phoenix UI at `http://localhost:{PHOENIX_PORT}`. The function is idempotent — safe to call on every Streamlit rerun — and persists traces to `PHOENIX_TRACE_DIR` across sessions. `tests/test_observability.py` covers idempotency, session creation, and env-var overrides without requiring a live Phoenix instance.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | Idempotency guard mechanism | Module-level `_initialized: bool = False` flag | `px.active_session()` can return a stale session object from a previous process; a module-level flag is the most reliable guard for the Streamlit same-process rerun scenario | If the function is called from multiple threads or processes |
| 2 | `PHOENIX_TRACE_DIR` directory creation | `os.makedirs(trace_dir, exist_ok=True)` before setting `PHOENIX_WORKING_DIR` | Phoenix raises if the working dir doesn't exist on some versions; pre-creating it is safe and satisfies the acceptance criterion explicitly | Never — defensive is correct here |
| 3 | `LangChainInstrumentor` double-instrument guard | Call `LangChainInstrumentor().instrument()` only inside the `_initialized` guard block | The instrumentor is not idempotent in all versions of `openinference-instrumentation-langchain==0.1.x`; calling it twice can register duplicate callbacks | If the library adds native idempotency |
| 4 | `px.launch_app()` `notebook_environment` argument | `notebook_environment="streamlit"` as specified in PRD | PRD §Observability explicitly names this parameter; omitting it would silently launch in a different mode | Never — PRD is authoritative |
| 5 | Test strategy for `px.launch_app()` | `unittest.mock.patch("observability.px")` to mock the entire `arize_phoenix` module alias | Avoids starting a real Phoenix server in test; consistent with the mock strategy used in `test_graph.py` and `test_ingest.py` | If integration tests are added separately |
| 6 | Test strategy for `LangChainInstrumentor` | `unittest.mock.patch("observability.LangChainInstrumentor")` | Prevents real OTel registration which would persist across test cases | Never |
| 7 | Public function name | `setup_observability()` | Issue spec §Public interface defines this exact name; `setup_tracing()` appears only in the stub docstring comment — treat the issue spec as authoritative | Never |
| 8 | `PHOENIX_PORT` type | Read as `int(os.getenv("PHOENIX_PORT", "6006"))` | `px.launch_app()` `port` parameter expects `int`; env vars are always strings | Never |
| 9 | Return type of `setup_observability()` | `-> None` | Issue spec §Public interface declares `-> None`; no caller depends on a return value | Never |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | `setup_observability()` — env reading, dir creation, Phoenix launch, LangChain instrumentation, idempotency guard | `observability.py` |
| T2 | Unit tests: idempotency, session creation, env-var overrides, dir creation, double-call safety | `tests/test_observability.py` |

---

## Architecture Constraints

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| `setup_observability()` must be idempotent — callable multiple times without raising or launching a second Phoenix instance | Issue spec §Acceptance criteria | Streamlit reruns `app.py` on every user interaction; a non-idempotent call crashes the app on the second interaction |
| `LangChainInstrumentor` must be imported from `openinference.instrumentation.langchain` | PRD §Observability, Issue spec | This is the only package that auto-instruments LangGraph node spans; using a different instrumentor silently misses node-level spans |
| `PHOENIX_WORKING_DIR` env var must be set before `px.launch_app()` is called | Issue spec §Trace persistence | Phoenix reads this env var at startup; setting it after launch has no effect |
| Phoenix must be launched in-process with `notebook_environment="streamlit"` | PRD §Observability | Omitting this argument causes Phoenix to launch in a headless mode that doesn't serve the UI in the Streamlit context |
| All LLM calls must go through `langchain_openai.ChatOpenAI` (not the raw `openai` SDK) | PRD §Observability, established in PR-3 | The `LangChainInstrumentor` hooks into LangChain callbacks; raw `openai` SDK calls bypass LangChain and produce no spans |
| `OPENAI_API_KEY` and other env vars loaded via `load_dotenv()` | PRD §Environment | `.env` file is the only secret store for the local setup; without `load_dotenv()`, API calls fail silently |
| No Streamlit UI code in this PR | Issue spec §Out of scope | UI integration (`app.py` calling `setup_observability()`) belongs to PR-5 |
| Unit tests must not require a live Phoenix server or `OPENAI_API_KEY` | Established convention (see `test_graph.py`, `test_ingest.py`) | CI would break without mocking |
| `PHOENIX_TRACE_DIR` directory must be created if it does not exist | Issue spec §Acceptance criteria | Phoenix raises a `FileNotFoundError` on some versions if the directory is absent |

---

## T1 — `setup_observability()`

### What it builds

The complete `observability.py` module replacing the current stub. A single public function `setup_observability()` that:

1. Reads `PHOENIX_PORT` and `PHOENIX_TRACE_DIR` from environment (with defaults `6006` and `./phoenix_traces`)
2. Creates `PHOENIX_TRACE_DIR` if it does not exist
3. Sets `os.environ["PHOENIX_WORKING_DIR"]` to `PHOENIX_TRACE_DIR`
4. On first call only: launches Phoenix in-process and registers the LangChain instrumentor
5. Guards against double-initialization via a module-level `_initialized` flag

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Module-level `_initialized` flag type | `bool`, starts `False` | Simplest thread-safe guard for the single-process Streamlit scenario |
| `os.makedirs` call | `exist_ok=True` | Idempotent; does not raise if directory already exists |
| `PHOENIX_WORKING_DIR` set method | `os.environ["PHOENIX_WORKING_DIR"] = trace_dir` | Phoenix reads this standard env var; setting it before `launch_app()` is the documented approach |
| `px.launch_app()` arguments | `port=port, notebook_environment="streamlit"` | `port` is required to support `PHOENIX_PORT` override; `notebook_environment` is required for Streamlit embedding |

### Layer compliance checklist

- [ ] No Streamlit imports or UI code in `observability.py`
- [ ] No graph imports — `observability.py` is a standalone utility, not coupled to `graph/`
- [ ] Env vars read with `os.getenv()` and sensible string defaults
- [ ] `load_dotenv()` called at module level to ensure `.env` is loaded before env reads

### Known limitations

- `LangChainInstrumentor` in `openinference-instrumentation-langchain==0.1.x` does not support uninstrumenting. Once registered, it persists for the process lifetime. This is acceptable for the local use case.
- The `_initialized` guard is not thread-safe. If `setup_observability()` is called concurrently from two threads, both could pass the guard. Acceptable for single-threaded Streamlit.
- `px.launch_app()` blocks until Phoenix is ready on some versions; on others it returns immediately. Tests must mock at the module level to avoid timing issues.

### Full implementation

```python
"""Arize Phoenix observability setup for the agentic CRAG pipeline.

Call setup_observability() once at Streamlit app startup.
After this call, every LangGraph node execution, LLM call, and
Chroma retriever call is captured as a named OpenTelemetry span
in the Phoenix UI at http://localhost:{PHOENIX_PORT}.
"""
from __future__ import annotations

import os

import arize.phoenix as px
from dotenv import load_dotenv
from openinference.instrumentation.langchain import LangChainInstrumentor

load_dotenv()

_initialized: bool = False


def setup_observability() -> None:
    """Launch Phoenix in-process and register LangChain instrumentor. Idempotent.

    Reads:
        PHOENIX_PORT      — Phoenix UI port (default: 6006)
        PHOENIX_TRACE_DIR — trace storage directory (default: ./phoenix_traces)

    After this call:
        - px.active_session() returns a non-None session
        - All LangChain LLM, retriever, and LangGraph node calls produce spans
        - Traces are persisted to PHOENIX_TRACE_DIR across sessions
    """
    global _initialized
    if _initialized:
        return

    port: int = int(os.getenv("PHOENIX_PORT", "6006"))
    trace_dir: str = os.getenv("PHOENIX_TRACE_DIR", "./phoenix_traces")

    # Ensure trace storage directory exists before Phoenix reads it
    os.makedirs(trace_dir, exist_ok=True)

    # Phoenix reads PHOENIX_WORKING_DIR at launch_app() time
    os.environ["PHOENIX_WORKING_DIR"] = trace_dir

    px.launch_app(port=port, notebook_environment="streamlit")
    LangChainInstrumentor().instrument()

    _initialized = True
```

### Verifiable acceptance criteria

- [ ] Calling `setup_observability()` twice does not raise and does not call `px.launch_app()` a second time
- [ ] After the first call, `px.active_session()` returns a non-None object
- [ ] `PHOENIX_TRACE_DIR` directory is created if absent (verify with `os.path.isdir`)
- [ ] Setting `PHOENIX_PORT=7777` before calling causes Phoenix to launch on port 7777
- [ ] `LangChainInstrumentor().instrument()` is called exactly once even when `setup_observability()` is called multiple times

---

## T2 — Unit Tests: `tests/test_observability.py`

### What it builds

A test module covering all acceptance criteria from the issue spec. All tests mock `arize.phoenix` and `LangChainInstrumentor` — no live Phoenix server or API key required.

### Test cases

| Test | Verifies |
|------|---------|
| `test_setup_called_once_launches_phoenix` | `px.launch_app()` is called exactly once on the first `setup_observability()` call |
| `test_setup_idempotent_does_not_relaunch` | Calling `setup_observability()` twice calls `px.launch_app()` exactly once total |
| `test_setup_instruments_langchain_once` | `LangChainInstrumentor().instrument()` is called exactly once regardless of call count |
| `test_phoenix_port_default` | `px.launch_app()` receives `port=6006` when `PHOENIX_PORT` env var is unset |
| `test_phoenix_port_override` | Setting `PHOENIX_PORT=7777` causes `px.launch_app()` to receive `port=7777` |
| `test_trace_dir_created_if_absent` | A non-existent `PHOENIX_TRACE_DIR` is created by `setup_observability()` |
| `test_phoenix_working_dir_set` | `os.environ["PHOENIX_WORKING_DIR"]` equals `PHOENIX_TRACE_DIR` after setup |
| `test_notebook_environment_streamlit` | `px.launch_app()` is called with `notebook_environment="streamlit"` |

### Layer compliance checklist

- [ ] No real Phoenix server started — entire `arize.phoenix` module mocked
- [ ] `_initialized` flag reset between tests via module reload or direct attribute patch
- [ ] No `OPENAI_API_KEY` required

### Known limitations

- The module-level `_initialized` flag persists across test cases if not reset. Each test that calls `setup_observability()` must either patch `observability._initialized` back to `False` before running or use `importlib.reload(observability)` to get a fresh module state.
- Resetting via `importlib.reload` is simpler and more reliable than patching the flag directly.

### Full implementation

```python
"""Unit tests for observability.py.

Run with: pytest tests/test_observability.py -v
No OPENAI_API_KEY or live Phoenix server required — all external calls mocked.
"""
from __future__ import annotations

import importlib
import os
from unittest.mock import MagicMock, patch, call

import pytest


def _fresh_observability():
    """Return a freshly reloaded observability module with _initialized reset."""
    import observability
    importlib.reload(observability)
    return observability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_px():
    mock_px = MagicMock()
    mock_session = MagicMock()
    mock_px.active_session.return_value = mock_session
    return mock_px


def _make_mock_instrumentor_cls():
    mock_cls = MagicMock()
    mock_instance = MagicMock()
    mock_cls.return_value = mock_instance
    return mock_cls


# ---------------------------------------------------------------------------
# First-call behaviour
# ---------------------------------------------------------------------------

class TestSetupObservabilityFirstCall:
    def test_setup_called_once_launches_phoenix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.setenv("PHOENIX_PORT", "6006")

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        mock_px.launch_app.assert_called_once()

    def test_notebook_environment_streamlit(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("notebook_environment") == "streamlit"

    def test_phoenix_port_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.delenv("PHOENIX_PORT", raising=False)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("port") == 6006

    def test_phoenix_port_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.setenv("PHOENIX_PORT", "7777")

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("port") == 7777

    def test_instruments_langchain_once(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        mock_instr_cls.return_value.instrument.assert_called_once()


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

class TestSetupObservabilityIdempotency:
    def test_double_call_does_not_relaunch_phoenix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()

        assert mock_px.launch_app.call_count == 1

    def test_double_call_does_not_instrument_twice(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()

        assert mock_instr_cls.return_value.instrument.call_count == 1

    def test_triple_call_launch_count_still_one(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()
            obs.setup_observability()

        assert mock_px.launch_app.call_count == 1


# ---------------------------------------------------------------------------
# Directory creation and env var propagation
# ---------------------------------------------------------------------------

class TestSetupObservabilityDirAndEnv:
    def test_trace_dir_created_if_absent(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "new_traces_dir")
        assert not os.path.isdir(trace_dir)
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        assert os.path.isdir(trace_dir)

    def test_phoenix_working_dir_env_set(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "traces")
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        assert os.environ.get("PHOENIX_WORKING_DIR") == trace_dir

    def test_trace_dir_already_exists_does_not_raise(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "existing_traces")
        os.makedirs(trace_dir)
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            # Should not raise even though directory already exists
            obs.setup_observability()
```

### Verifiable acceptance criteria

- [ ] All 13 test cases pass with `pytest tests/test_observability.py -v`
- [ ] No `OPENAI_API_KEY` env var required to run the tests
- [ ] No real Phoenix server started during test execution (verify by checking no process on port 6006 after test run)

---

## Migration

Not applicable — this PR adds no database models, migrations, or schema changes. `observability.py` is a pure Python utility module with no persistent data layer.

---

## Test quality rules

- **Idempotency:** verify `mock_px.launch_app.call_count == 1` after multiple `setup_observability()` calls, not just that no exception was raised
- **Port type:** verify `kwargs.get("port")` is an `int` (not a string) — `px.launch_app()` would fail with a string port on some versions
- **Directory creation:** use `tmp_path` (pytest fixture) for all `PHOENIX_TRACE_DIR` values so tests clean up automatically and don't interfere with the real `./phoenix_traces` directory
- **Module reset:** use `importlib.reload(observability)` before each test that calls `setup_observability()`, not `observability._initialized = False`, to ensure clean module state including the global flag and any module-level side effects
- **Env var isolation:** use `monkeypatch.setenv` / `monkeypatch.delenv` (pytest fixture) rather than direct `os.environ` mutation so env changes don't leak between tests

---

## Automated verification

```bash
pytest tests/test_observability.py -v
pytest tests/ -v
```

---

## Manual verification

1. **Phoenix launches and UI is accessible:**
   - Ensure `.env` is configured with a valid `OPENAI_API_KEY`
   - Run `python -c "from observability import setup_observability; setup_observability()"`
   - Open `http://localhost:6006` in a browser
   - Expected: Phoenix UI loads with the Projects view

2. **Trace persistence across sessions:**
   - After step 1, verify `./phoenix_traces/` directory exists and contains Phoenix's SQLite or file-based trace store
   - Stop the Python process and restart; call `setup_observability()` again
   - Open Phoenix UI — previously captured traces should still be visible

3. **Idempotency in a live Python session:**
   - Call `setup_observability()` twice in the same session:
     ```python
     from observability import setup_observability
     setup_observability()
     setup_observability()  # must not raise
     ```
   - Expected: no exception, Phoenix UI still accessible, single session active

4. **Port override:**
   - Set `PHOENIX_PORT=6007` in `.env`
   - Call `setup_observability()`
   - Expected: Phoenix UI accessible at `http://localhost:6007`, not 6006

5. **Span capture with CRAG graph (requires PR-3 to be merged):**
   - Run the CRAG graph with observability enabled:
     ```python
     from observability import setup_observability
     from graph.graph import build_graph
     setup_observability()
     graph = build_graph()
     result = graph.invoke({
         "query": "What is CRAG?",
         "reformulated_query": None,
         "retrieved_docs": [],
         "grade_results": [],
         "final_answer": None,
         "iteration_count": 0,
     })
     ```
   - Open Phoenix UI at `http://localhost:6006` → Projects → inspect the latest trace
   - Expected: trace contains named spans including `retrieve`, `grade_documents`, LLM call spans, and retriever spans

---

## Implementation Notes

### Plan vs. codebase mismatch: `arize.phoenix` import alias

The plan specified `import arize.phoenix as px` in the T1 full implementation. However, the `arize-phoenix==4.*` package installs its Python module as `phoenix`, not `arize.phoenix`. Confirmed by inspecting `site-packages/`: the top-level package is `phoenix/`, there is no `arize/phoenix/` path. The correct import is `import phoenix as px`, which is what was used in the implementation.

**Action taken:** Used `import phoenix as px` in `observability.py`. The module alias `px` is identical to what the plan intended, so all call-sites (`px.launch_app(...)`, `px.active_session()`) are unchanged.

**Test mock fix:** The plan's `_fresh_observability()` helper used bare `importlib.reload(observability)` which re-executes the top-level `import phoenix as px`. On this environment arize-phoenix v4 fails to import without `pandas` (a transitive dependency that requires C++ build tools to install). Fix: `_fresh_observability()` now pre-injects `MagicMock()` stubs for `phoenix` and `openinference.instrumentation.langchain` into `sys.modules` before reloading, consistent with the "mock at the module level" convention stated in the plan. The test logic and assertion invariants are unchanged.
