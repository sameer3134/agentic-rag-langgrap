# PR Review: feat/streamlit-ui

**Branch:** `feat/streamlit-ui`
**Plan file:** `thoughts/shared/plans/PR5-streamlit-ui.md`
**Reviewer:** Claude Sonnet 4.6
**Date:** 2026-06-14

---

## Review Summary

The implementation in the working tree (`app.py`, `tests/test_app.py`) correctly fulfils the majority of the plan's acceptance criteria. The code is well-structured, presentation-layer only, and matches the plan's design decisions. One critical issue blocks merging: the implementation files are not committed to the branch.

---

## 1. Critical — must fix before merging

### C1 — Implementation files are uncommitted

`app.py`, `tests/test_app.py`, and `thoughts/shared/plans/PR5-streamlit-ui.md` exist only in the working tree and are not staged or committed to `feat/streamlit-ui`. Running `git diff origin/feat/observability...HEAD` shows no PR5 changes; `git status` shows `app.py` as modified (unstaged) and `tests/test_app.py` plus the plan file as untracked.

**Impact:** The branch as pushed to the remote contains only the 4-line stub (`app.py`) from prior commits. Anyone reviewing the remote branch sees no Streamlit UI implementation. No CI would run `tests/test_app.py`.

**Fix:** Stage and commit the three files:
```bash
git add app.py tests/test_app.py thoughts/shared/plans/PR5-streamlit-ui.md
git commit -m "feat: Streamlit UI for ingestion and querying (PR-5)"
```

---

## 2. Important — should fix

### I1 — Cache-idempotency test missing

The plan's "Test quality rules" section explicitly requires: *"verify idempotency by calling `_init_resources()` twice in a mocked context and asserting `build_graph` was called only once — not just that no exception was raised."* Only one test exists (`test_graph_exception_displays_st_error`); there is no test that calls `_init_resources()` twice and asserts `build_graph` mock call count equals 1.

`AppTest` isolates cache state, so this test requires direct unit-testing of `_init_resources()` with `st.cache_resource.clear()` between calls (or using `st.cache_resource` reset before the second call).

**Impact:** If `@st.cache_resource` is accidentally removed, or if the function is refactored to not use it, the regression would not be caught by the current test suite.

**Fix:** Add a second test in `tests/test_app.py`:
```python
def test_init_resources_called_once_across_reruns(self, tmp_path, monkeypatch):
    """_init_resources() must call build_graph only once across multiple invocations."""
    # ... set up env vars ...
    with patch("graph.graph.build_graph", return_value=MagicMock()) as mock_build, \
         patch("observability.setup_observability"), \
         patch("langchain_openai.OpenAIEmbeddings", return_value=MagicMock()), \
         patch("langchain_community.vectorstores.Chroma", return_value=MagicMock()):
        import app
        app._init_resources.clear()  # ensure clean state
        app._init_resources()
        app._init_resources()  # second call — should be a cache hit
    assert mock_build.call_count == 1
```

### I2 — `_vectorstore` returned but never used in `app.py`

`_init_resources()` returns `(vectorstore, graph)` and `app.py` unpacks it as `_vectorstore, graph = _init_resources()`. However, `_vectorstore` is never referenced anywhere in the app — the graph holds its own internal retriever via `graph/nodes.py`'s `_get_retriever()`. The vectorstore object is initialised, connected to Chroma, and immediately discarded.

This is not a correctness bug (the app works without using `_vectorstore`), but it is an architectural confusion: the plan's T1 design decision states the vectorstore is returned "so the rest of the app can reference them without re-importing from sub-modules." No part of the app actually references it. This creates a false impression that the app uses a shared vectorstore when in fact it relies on the graph's internal retriever.

**Impact:** Minor resource waste (one Chroma connection initialised unnecessarily); misleading architecture comment.

**Fix (option A):** Return only `graph` from `_init_resources()` if the vectorstore is not needed at the app layer.
**Fix (option B):** Pass `_vectorstore` to `ingest_pdfs` to share the connection (requires `ingest_pdfs` API change — out of scope for this PR).

---

## 3. Minor — consider fixing

### M1 — `st.stop()` absent from exception handler

Assumption #4 in the plan states: *"`st.stop()` prevents blank output below the error message."* The final implementation (both in the plan's "Full app.py Implementation" section and in the actual `app.py`) omits `st.stop()`. The behaviour is acceptable since the `if user_query:` block ends after the `except` clause, but the plan/assumption is inconsistent with the code.

No blank output can appear below the error because `st.markdown` and `_render_debug_panel` are inside the `try` block and will not execute on exception. However, for defensive completeness and consistency with the stated assumption, adding `st.stop()` after `st.error(str(e))` is low-risk.

### M2 — `Path("data/uploads").mkdir()` called on every rerun

`Path("data/uploads").mkdir(parents=True, exist_ok=True)` is at the module level of `app.py` (not inside the `if uploaded_files:` block or `_init_resources()`). Streamlit re-executes module-level code on every rerun, meaning this `mkdir` call runs on every page rerun even when no files are being uploaded. The `exist_ok=True` flag makes this safe but it is a minor inefficiency. The plan's Assumption #3 says it should be called "at the top of the upload handler, not at module load" — the implementation places it at module load, contradicting the assumption.

### M3 — `ingest_pdfs` lazy import removed (plan inconsistency)

The plan's T2 snippet uses `from ingest import ingest_pdfs` as a lazy import inside the `if uploaded_files: if st.button("Ingest"):` block. The final `app.py` imports it at the top of the file (`from ingest import ingest_pdfs` on line 22). This is actually better practice (top-level imports are preferable to lazy imports) and the plan itself includes it in the "Full app.py Implementation" at the top. The T2 snippet is stale but it is only a plan inconsistency, not a code issue.

---

## 4. Positive Findings

- **Layer compliance:** `app.py` contains zero business logic, zero LLM calls, and zero direct Chroma queries. All logic is delegated to `ingest_pdfs`, `build_graph`, and `setup_observability`. This is exactly the separation described in the architecture constraints.

- **`@st.cache_resource` correctly applied:** The function uses `@st.cache_resource` (not `@st.cache_data`), and `setup_observability()` is called before `build_graph()` inside the cached function — both explicit constraints from the plan.

- **All six `CRAGState` keys supplied:** The graph invocation at line 130–138 supplies all six keys (`query`, `reformulated_query`, `retrieved_docs`, `grade_results`, `final_answer`, `iteration_count`) with correct zero-value defaults, satisfying the "missing keys cause KeyError" constraint.

- **Grade threshold matches `nodes.py`:** The `score >= 0.7` threshold in `_render_debug_panel` correctly mirrors `GRADE_THRESHOLD = 0.7` in `graph/nodes.py`.

- **Test isolation:** `tests/test_app.py` uses `monkeypatch.setenv("OPENAI_API_KEY", "test-key")` and stubs all phoenix sub-modules, satisfying "unit tests must not require OPENAI_API_KEY or live Phoenix server."

- **`from __future__ import annotations`** present at the top of both `app.py` and `tests/test_app.py`.

- **Import order** follows stdlib → third-party → `app.*` convention throughout `app.py`.

- **`st.expander("Debug / Trace", expanded=False)`** correctly implements the "collapsed by default" acceptance criterion.

- **`st.markdown`** used for final answer display (not `st.write`), satisfying the explicit plan requirement.

---

## Verdict

```
Verdict: NEEDS_WORK

Critical issues  : 1  (C1 — uncommitted files)
Important issues : 2  (I1 — missing idempotency test, I2 — unused vectorstore)
Minor issues     : 3  (M1, M2, M3 — all low-risk)

NEEDS_WORK — Important issues found. Stage and commit the implementation files (C1),
             add the cache-idempotency test (I1), and address the unused vectorstore
             (I2) before opening a PR.
```

Review written: `thoughts/shared/reviews/streamlit-ui-review.md`
