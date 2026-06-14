# PR Review — feat/crag-graph

**Branch:** `feat/crag-graph`
**Plan:** `thoughts/shared/plans/PR3-crag-graph.md`
**Reviewed:** 2026-06-14
**Reviewer:** Claude Sonnet 4.6 (automated multi-axis review)

---

## Plan Coverage

The plan file PR3-crag-graph.md was found and read in full. All eight tasks (T1–T8) were cross-checked against the implementation.

---

## 1. Critical — must fix before merging

No critical issues found. No data loss, security vulnerabilities, broken graph wiring, or failed acceptance criteria were identified.

---

## 2. Important — should fix

### I-1: `_get_retriever()` function name misleads the test isolation contract

**File:** `graph/nodes.py` (line 31)

`_get_retriever()` returns a `Chroma` vectorstore object, not a LangChain retriever (which would be obtained via `.as_retriever()`). The `retrieve` node calls `.similarity_search()` directly on the returned object. The docstring says "Return a Chroma vectorstore" which contradicts the function name.

This is a naming violation that affects future maintainers: if a developer renames it to return a true retriever (via `.as_retriever()`), `retrieve` will break because retrievers expose `.invoke()` / `.get_relevant_documents()`, not `.similarity_search()`. The test correctly patches `_get_retriever` and calls `.similarity_search()`, so this functions correctly now — but the misleading name is a latent trap.

**Fix:** Rename `_get_retriever` to `_get_vectorstore` to match the pattern established in `ingest.py` (Assumption #1 in the plan explicitly references mirroring the `_get_vectorstore()` pattern).

### I-2: `reformulate_query` selects from all grade results, not only failing ones

**File:** `graph/nodes.py` (line 101–103)

```python
best_failed = max(grade_results, key=lambda r: r["score"])
reason = best_failed["reason"]
```

The variable is named `best_failed` but the `max()` call ranges over *all* `grade_results`, including passing ones. In normal flow this is harmless because `reformulate_query` is only called when all docs fail. However:

- The variable name `best_failed` falsely implies it was filtered to failing docs.
- If state is ever inconsistent (e.g., a future change routes to `reformulate_query` even when some docs pass), the reformulation prompt will use the reason from the highest-scoring *passing* doc, which is semantically wrong.

**Fix:** Either add a comment clarifying the invariant ("only called when all docs fail, so all results are failing"), or defensively filter: `failed_results = [r for r in grade_results if not r["relevant"]]` and use `max(failed_results, ...)` with a fallback.

---

## 3. Minor — consider fixing

### M-1: Unused `Any` import in `graph/nodes.py`

**File:** `graph/nodes.py` (line 6)

```python
from typing import Any
```

`Any` is imported but never referenced in `nodes.py`. It is used correctly in `graph/graph.py`. Remove the unused import to keep the file clean and avoid linter warnings.

### M-2: Unused `pytest` import in `tests/test_graph.py`

**File:** `tests/test_graph.py` (line 11)

```python
import pytest
```

`pytest` is imported but not used (no `pytest.raises`, `pytest.mark`, or `pytest.fixture` calls appear in the file). Remove to avoid `F401` linter warning.

### M-3: `_get_retriever()` constructs a new `OpenAIEmbeddings` and `Chroma` client on every `retrieve` call

**File:** `graph/nodes.py` (line 31–39)

The plan acknowledges this in Assumption #1 ("Avoids constructing a new Chroma client on every node invocation") and states the factory is "cached at call time". However, `_get_retriever()` as implemented creates a fresh `OpenAIEmbeddings` and `Chroma` instance on every invocation — there is no caching. In the reformulation loop this is called 1–3 times per graph invocation. For now the overhead is acceptable, but the plan's claim of "cached at call time" is not implemented.

**Fix (optional):** Add `functools.lru_cache(maxsize=1)` or a module-level `_VECTORSTORE: Chroma | None = None` sentinel pattern to actually cache across calls.

### M-4: `test_iteration_count_never_exceeds_2` assertion allows `iteration_count == 2` but comment says "stop at 2"

**File:** `tests/test_graph.py` (line 395)

```python
assert result["iteration_count"] <= 2
```

The assertion is correct — `iteration_count` can legitimately reach 2 (the loop runs at iterations 0 and 1, increments to 1 and 2, then at `iteration_count == 2` the router returns `not_found`). The test description says "must stop at 2" which is consistent. No change needed, but a comment clarifying the expected final value (`== 2` after two reformulations) would make the intent clearer.

---

## 4. Positive findings

- **Correctness of Python-recomputed `relevant` field:** `grade_documents` ignores the LLM's `relevant` bool entirely and recomputes from `output.score >= GRADE_THRESHOLD`. This is the correct defensive pattern and it is tested explicitly (`test_relevant_computed_from_score_not_trusted_from_llm`).

- **Exact threshold boundary tested:** `test_returns_generate_at_exact_threshold` and `test_below_threshold_does_not_trigger_generate` cover `score == 0.7` (passes) and `score == 0.69` (fails), which are the most common sources of off-by-one bugs in threshold logic.

- **`not_found` string format exactly matches spec:** The f-string `f"(Best relevance score: {best['score']:.2f} — reason: '{best['reason']}')"` matches the issue spec verbatim, including the em-dash (`—`) and single-quote wrapping of the reason.

- **Import hygiene:** Both `graph/nodes.py` and `graph/graph.py` correctly open with `from __future__ import annotations`. Import order is stdlib → third-party → local in both files.

- **State immutability:** No node mutates the input `state` dict in-place. All return partial dicts. The LangGraph merge contract is satisfied.

- **No Phoenix instrumentation added:** The constraint "No Arize Phoenix instrumentation in this PR" (out of scope for PR-4) is correctly respected.

- **Test isolation:** All LLM calls and the Chroma retriever are mocked via `unittest.mock.patch`. No `OPENAI_API_KEY` is required to run the test suite.

- **`route_after_grading` is pure:** No LLM calls, no I/O, no side effects. Deterministic given the same state.

- **Reformulation uses original query:** `reformulate_query` correctly uses `state["query"]` (the original) for the prompt rather than `state.get("reformulated_query")`, preventing prompt drift across reformulation iterations.

---

## Acceptance Criteria Coverage

| Criterion | Status |
|-----------|--------|
| `route_after_grading` returns `"generate"` when any doc passes | PASS |
| `route_after_grading` returns `"reformulate_query"` at iter 0 and 1 | PASS |
| `route_after_grading` returns `"not_found"` at iter 2 | PASS |
| `not_found` exact string: `"Best relevance score:"`, 2dp score, verbatim reason | PASS |
| `generate` filters to docs with `score >= 0.7` only | PASS |
| `grade_documents` one result per doc, `relevant=True` iff `score >= 0.7` | PASS |
| `build_graph()` compiles without raising | PASS |
| Full graph invocation with mocked deps returns non-None `final_answer` | PASS |
| Reformulation loop cap: `iteration_count <= 2` | PASS |
| No Arize Phoenix in this PR | PASS |
| Tests require no `OPENAI_API_KEY` | PASS |
| `from __future__ import annotations` at top of every new file | PASS |
| `langchain_core.documents.Document` (not `langchain.schema`) | PASS |
| `langchain_openai.ChatOpenAI` (not raw openai SDK) | PASS |
| Collection name `"crag_corpus"` | PASS |

---

## Summary

The implementation is functionally correct and complete. All acceptance criteria from the issue spec and plan are satisfied. The two important issues (I-1 and I-2) are naming/defensive-coding concerns that do not cause failures under normal operating conditions but represent latent traps for future maintainers.

```
Review written: thoughts/shared/reviews/crag-graph-review.md
Verdict: NEEDS_WORK

If NEEDS_WORK: fix the important findings, then re-run /pr-review
```

---

## Verdict

```
Verdict: NEEDS_WORK
```

**Reason:** Two important issues found (I-1: misleading `_get_retriever` name violates the plan's own stated pattern; I-2: `best_failed` selection includes passing docs, creating a semantic mismatch). No critical issues. Safe to fix and re-review.
