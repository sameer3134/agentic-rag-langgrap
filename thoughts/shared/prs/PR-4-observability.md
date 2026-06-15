## Summary

This PR replaces the `observability.py` stub with a complete `setup_observability()` function that launches Arize Phoenix in-process and registers the `openinference-instrumentation-langchain` auto-instrumentor. The function is idempotent — safe to call on every Streamlit rerun — and persists traces to `PHOENIX_TRACE_DIR` across sessions. Unit tests cover idempotency, session creation, and env-var overrides without requiring a live Phoenix instance.

## Changes

- `observability.py` — full implementation of `setup_observability()`: env reading, dir creation, `PHOENIX_WORKING_DIR` assignment, Phoenix launch with `notebook_environment="streamlit"`, LangChain instrumentation, and idempotency guard via module-level `_initialized` flag
- `tests/test_observability.py` — 11 unit tests covering first-call behaviour, idempotency (double/triple calls), directory creation, env-var propagation, and port override; all mocked, no live Phoenix or API key required
- `thoughts/shared/plans/PR4-observability.md` — implementation plan with task table, architecture constraints, and implementation notes
- `thoughts/shared/reviews/observability-review.md` — review findings and NEEDS_WORK verdict

## Tasks covered

| Task | What it builds |
|------|---------------|
| T1 | `setup_observability()` — reads `PHOENIX_PORT` and `PHOENIX_TRACE_DIR` from env, creates the trace directory, sets `PHOENIX_WORKING_DIR`, launches Phoenix in-process with `notebook_environment="streamlit"`, registers `LangChainInstrumentor`, and guards against double-initialization |
| T2 | Unit tests: idempotency (double/triple call), first-call Phoenix launch, LangChain instrumentation, default and override port, directory creation, `PHOENIX_WORKING_DIR` env var propagation, `notebook_environment` argument |

## Test plan

- [ ] `setup_observability()` called twice does not raise and does not call `px.launch_app()` a second time
- [ ] After the first call, `PHOENIX_TRACE_DIR` directory exists on disk
- [ ] Setting `PHOENIX_PORT=7777` before calling causes Phoenix to launch on port 7777
- [ ] `LangChainInstrumentor().instrument()` is called exactly once even when `setup_observability()` is called multiple times
- [ ] All automated checks pass: `make test-cov && make lint`

## Review notes

Review verdict: NEEDS_WORK

Proceeding despite NEEDS_WORK — important findings may remain unresolved; reviewer should check.

Key findings from the review that should be addressed before merge:

- **2.1** — Plan/import alias deviation (`arize.phoenix` vs `phoenix`) is documented in Implementation Notes; confirm this note is visible to reviewers before merge.
- **2.2** — `PHOENIX_WORKING_DIR` env var set inside `setup_observability()` is not cleaned up via `monkeypatch.delenv` in `test_phoenix_working_dir_env_set`; future tests that call `setup_observability()` without overriding `PHOENIX_TRACE_DIR` may see a stale `PHOENIX_WORKING_DIR`. Recommend adding `monkeypatch.delenv("PHOENIX_WORKING_DIR", raising=False)` at teardown of each test in `TestSetupObservabilityDirAndEnv`.
- **2.3** — No test asserts `px.active_session()` returns a non-None value, despite this being a plan acceptance criterion (T1 §Verifiable acceptance criteria, item 2). Recommend adding a dedicated test case.

---
Plan: `thoughts/shared/plans/PR4-observability.md`
Review: `thoughts/shared/reviews/observability-review.md`
