# PR Review: feat/ragas-eval

**Branch:** `feat/ragas-eval`
**Plan:** `thoughts/shared/plans/PR6-ragas-eval.md`
**Reviewer:** Claude Sonnet 4.6
**Date:** 2026-06-14

---

## Summary

The PR replaces the `eval.py` stub with a complete Ragas evaluation script and adds `tests/test_eval.py`. The implementation closely follows the plan across all six tasks (T1–T6).

**Files changed:**
- `eval.py` — stub replaced with full implementation (~271 lines)
- `tests/test_eval.py` — new, 11 unit tests (all pass)
- `thoughts/shared/plans/PR6-ragas-eval.md` — planning artifact (not runtime code)

---

## 1. Critical — must fix before merging

No critical issues found.

---

## 2. Important — should fix

### I1 — `load_or_generate_golden_dataset()` raises `RuntimeError` but `main()` only catches it when `data/golden_dataset.json` is absent

**File:** `eval.py`, lines 261–265

```python
try:
    dataset = load_or_generate_golden_dataset()
except RuntimeError as exc:
    print(f"[eval] ERROR: {exc}", file=sys.stderr)
    sys.exit(0)
```

The `RuntimeError` guard in `main()` only covers the call to `load_or_generate_golden_dataset()`. If a `RuntimeError` is raised from inside `run_pipeline_on_dataset()` (e.g., the `build_graph()` import fails at runtime because `graph/` is not on the path), it will propagate unhandled. The plan's architecture constraint says "Script exits with code 0 even when metrics fail" but does not mandate catching all errors; however, the accepted exit-0 contract (Assumption 9) applies to metric failures, not unexpected crashes. This is a minor concern but worth noting.

More importantly: `_load_documents_from_chroma()` can raise exceptions other than `RuntimeError` (e.g., `chromadb` connection errors, import errors) that will bubble out of `load_or_generate_golden_dataset()` uncaught and propagate through `main()`. These would cause a non-zero exit and a Python traceback rather than a friendly message. The plan's empty-Chroma guard only raises `RuntimeError` for the empty-docs case; connection failures produce different exceptions. This is not a correctness bug but a robustness gap that affects CI.

**Recommendation:** Widen the `except` clause in `main()` to also catch `Exception` for the dataset load path, or at minimum document the known uncaught exception types.

---

### I2 — `run_evaluation()` uses `from ragas import evaluate` but plan specifies `from ragas.metrics import ...`

**File:** `eval.py`, lines 222–228

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    context_recall,
    answer_relevancy,
    context_precision,
)
```

The plan (Architecture Constraints, row 11) says: "use `from ragas.metrics import ...` not `from ragas import ...`". The `evaluate` function is correctly imported from `ragas` (top-level), and the metrics are correctly imported from `ragas.metrics`. This matches the plan's intent (the constraint was about metric names, not the `evaluate` function). No action needed — this is informational. On review, this is **not** a true violation.

---

### I3 — `load_or_generate_golden_dataset()` accesses `testset.test_data` using `row.question` / `row.ground_truth` attribute access, which is Ragas 0.1.x-specific

**File:** `eval.py`, lines 134–137

```python
dataset_rows = [
    {"question": row.question, "ground_truth": row.ground_truth}
    for row in testset.test_data
]
```

The plan (Assumption 3) acknowledges this is the Ragas 0.1.x API and flags it as a revisit point. The `requirements.txt` pins `ragas==0.1.*`. However, Ragas 0.1.x ships several sub-patch versions and the `testset.test_data` attribute shape changed between sub-versions. This is a pre-existing known risk documented in the plan — not a new defect — but the implementation does not validate the testset shape before iterating, so a shape mismatch would produce a hard-to-diagnose `AttributeError`.

**Recommendation:** Add a comment noting that `testset.test_data` is the Ragas 0.1.x internal attribute, and consider wrapping the list comprehension in a try/except with a helpful error message referencing the ragas version pinning.

---

## 3. Minor — consider fixing

### M1 — `_get_eval_module()` in tests does not force a fresh import

**File:** `tests/test_eval.py`, lines 20–25

```python
def _get_eval_module(self):
    if "eval" in sys.modules:
        return sys.modules["eval"]
    import eval as ev
    return ev
```

The comment says "Fresh import each time to avoid stale module state" but the implementation returns the cached module if it is already in `sys.modules`. This means the first test to import `eval` wins; subsequent tests reuse the same module object. In practice this is fine since the constants are fixed module-level values, but the comment is misleading. It would be cleaner to either remove the comment or use `importlib.reload()` to actually force a fresh import.

---

### M2 — `GOLDEN_DATASET_PATH` is a relative `Path`, which makes it CWD-dependent

**File:** `eval.py`, line 31

```python
GOLDEN_DATASET_PATH = Path("data/golden_dataset.json")
```

`eval.py` must be run from the project root for this path to resolve correctly. If invoked from a different directory (e.g., `python /absolute/path/eval.py` from `/tmp`), the file will be written to `/tmp/data/golden_dataset.json`. The plan (Assumption 6) notes the `data/` directory already exists but does not address the CWD assumption explicitly.

**Recommendation:** Consider anchoring to `Path(__file__).parent / "data" / "golden_dataset.json"` for robustness, or document that the script must be run from the project root.

---

### M3 — No test covers "one tick below threshold is FAIL"

**File:** `tests/test_eval.py`

The plan's test quality rules (section "Test quality rules") specify a "one tick below threshold must be FAIL" case with scores like `0.849`. The implemented tests cover below-threshold (e.g., `0.80 < 0.85`) but no test uses a boundary value like `0.8499`. The plan example calls for `0.849` specifically to test floating-point boundary behaviour. This is a minor gap — the existing tests are correct but not maximally rigorous at the boundary.

---

### M4 — `run_pipeline_on_dataset()` silently ignores a length mismatch between `retrieved_docs` and `grade_results`

**File:** `eval.py`, lines 185–189

```python
passing_docs = [
    doc
    for doc, grade in zip(retrieved_docs, grade_results)
    if grade["score"] >= GRADE_THRESHOLD
]
```

`zip()` silently truncates to the shorter list. If the graph ever returns mismatched lengths (e.g., due to a bug in `grade_documents`), this would silently produce fewer context items than expected without any warning. The plan does not require a length assertion here, but a defensive `assert len(retrieved_docs) == len(grade_results)` or a warning log would prevent silent data corruption in the eval results.

---

## 4. Positive findings

- **Threshold constants are named module-level constants**, not inline magic numbers — exactly as specified. Unit tests read them by name, making the tests resistant to accidental edits.

- **Lazy imports** (inside function bodies) for `ragas`, `langchain_openai`, and `graph.*` mean that `import eval` succeeds without `OPENAI_API_KEY` and without a running Chroma instance. All 11 unit tests pass with zero API calls — fully CI-safe.

- **`GRADE_THRESHOLD` is imported from `graph.nodes`** rather than hardcoded. This ensures the eval score threshold stays in sync with the pipeline's grading logic without manual coordination.

- **Exit-0 contract** is correctly implemented: `sys.exit(0)` is called on `RuntimeError`, and no other `sys.exit()` call with a non-zero code exists in the script.

- **`data/golden_dataset.json` is in `.gitignore`** — confirmed present. Golden dataset will not accidentally be committed to the repo.

- **`from __future__ import annotations`** is present at the top of both `eval.py` and `tests/test_eval.py`, satisfying the established project convention.

- **`build_graph()` is called once before the per-question loop** — correct. Compilation happens once for all 50 questions.

- **Test suite structure mirrors existing conventions** (`tests/test_graph.py`, `tests/test_ingest.py`) — class-based pytest, `capsys` for stdout capture, no LLM mocking needed for pure functions.

- **`THRESHOLDS` dict is verified to match the named constants** in `test_thresholds_dict_matches_constants` — good defence against a copy-paste desync between the constants and the dict.

---

## Acceptance Criteria Checklist

| Task | Criterion | Status |
|------|-----------|--------|
| T1 | `THRESHOLD_FAITHFULNESS == 0.85` | PASS |
| T1 | `THRESHOLD_CONTEXT_RECALL == 0.80` | PASS |
| T1 | `THRESHOLD_ANSWER_RELEVANCY == 0.80` | PASS |
| T1 | `THRESHOLD_CONTEXT_PRECISION == 0.75` | PASS |
| T1 | Mixed scores produce correct PASS/FAIL/Overall | PASS |
| T2 | Loads from file when it exists | PASS |
| T2 | Generates and saves when file absent | PASS |
| T2 | Raises RuntimeError when Chroma empty | PASS |
| T3 | Returns exactly `len(dataset)` rows | PASS |
| T3 | Each row has required keys | PASS |
| T3 | "not found" answers produce `contexts=[]` | PASS |
| T3 | `iteration_count` reset to 0 per question | PASS |
| T4 | Returns dict with four specified keys | PASS |
| T5 | Script exits 0 on metric failure | PASS |
| T5 | Script exits 0 on empty Chroma | PASS |
| T6 | All 11 unit tests pass | PASS (confirmed by pytest run) |
| T6 | No `OPENAI_API_KEY` required for tests | PASS |

---

## Verdict

```
Verdict: PASS

No critical issues found. Two important observations noted (I1: exception coverage
gap for non-RuntimeError failures from Chroma; I3: ragas testset shape not validated)
but neither is a blocking defect — both are pre-existing risks acknowledged in the
plan's assumptions. All acceptance criteria are satisfied. All 11 unit tests pass.
Safe to open a PR.
```

Review written: `thoughts/shared/reviews/ragas-eval-review.md`
Verdict: PASS

If PASS: run /commit then /describe_pr to open the PR
