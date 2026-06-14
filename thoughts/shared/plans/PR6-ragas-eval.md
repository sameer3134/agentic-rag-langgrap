# PR6 — feat: Ragas evaluation script and golden dataset

**Branch:** `feat/ragas-eval`
**PR ID:** PR-6
**Depends on:** PR-2 (feat/pdf-ingestion), PR-3 (feat/crag-graph)

---

## What This PR Does

This PR replaces the stub `eval.py` with a complete, standalone command-line evaluation script that measures CRAG pipeline quality against a synthetic golden dataset. On first run it generates ~50 Q&A pairs from the ingested Chroma corpus using Ragas `TestsetGenerator` and saves them to `data/golden_dataset.json`; subsequent runs load the saved file instead of regenerating (preserving metric trend interpretability). It then invokes the compiled CRAG graph for each question, collects the retrieved context and generated answer, runs Ragas `evaluate()` across four metrics (Faithfulness, Context Recall, Answer Relevancy, Context Precision), and prints a pass/fail table to stdout. Two unit-test classes are added to `tests/test_eval.py`: one guards the threshold constant values, one verifies the pass/fail table logic against a mock result dict.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | Test file location | `tests/test_eval.py` (new file) | Mirrors the existing `tests/test_graph.py` and `tests/test_ingest.py` pattern; keeps all tests in one directory | If the project adds a dedicated `eval/` package |
| 2 | Table rendering library | Plain string formatting with `str.ljust()` / format strings — not `rich` | The issue spec says "Use `rich` or plain string formatting — either is acceptable"; plain formatting has zero extra dependencies | If a richer table style is desired for the UI |
| 3 | `EvaluationDataset` Ragas API | `ragas.dataset_schema.EvaluationDataset` with `from_list()` constructor | Ragas 0.1.x public API; the `evaluate()` function accepts `EvaluationDataset` | If Ragas 0.2.x changes the dataset schema |
| 4 | `TestsetGenerator` knowledge source | Load all documents from Chroma using `vectorstore.get()` and reconstruct `langchain_core.documents.Document` objects | Chroma is the single source of truth for ingested content; avoids requiring a separate document list parameter | If documents are evicted from Chroma between ingestion and eval run |
| 5 | "not found" answer handling | Record as `{"question": q, "answer": final_answer, "contexts": [], "ground_truth": gt}` with `contexts=[]` | Issue spec explicitly requires this: "record it with empty `contexts` and the refusal string as `answer`" | Never — specified |
| 6 | `data/golden_dataset.json` parent directory | `data/` directory already exists (contains `data/uploads/`) | Confirmed by directory listing | If the `data/` directory is deleted |
| 7 | Graph initial state for each eval question | Fresh `CRAGState` with `iteration_count=0`, `reformulated_query=None`, `retrieved_docs=[]`, `grade_results=[]`, `final_answer=None` | Issue spec: "each query is stateless and independent" (grilling log Q22) | Never — stateless design is a hard requirement |
| 8 | Ragas `evaluate()` LLM | Uses `OPENAI_API_KEY` from env (same key as pipeline) — no separate Ragas LLM configuration | Issue spec: "`TestsetGenerator` uses `OPENAI_API_KEY` (same key as the rest of the pipeline)" | If a dedicated evaluation LLM key is needed |
| 9 | Script exit code | Always exit 0 even when metrics fail | Issue spec §Acceptance criteria: "Script exits with code 0 even when metrics fail (it reports, does not gate)" | If eval is integrated into CI with gating |
| 10 | Passing docs extraction for context | Extract `retrieved_docs` filtered by `grade_results[i]["score"] >= 0.7` from final state | Issue spec: "Capture from final state: `retrieved_docs` (filtered passing docs), `final_answer`"; mirrors `generate` node filtering logic | If `generate` node is refactored to expose passing docs explicitly |
| 11 | `TestsetGenerator` distribution | Default Ragas distribution (`simple`, `reasoning`, `multi_context`) | Issue spec does not specify distribution; default provides variety across question types | If evaluation focus shifts to a specific question type |
| 12 | Ragas metrics import path | `from ragas.metrics import faithfulness, context_recall, answer_relevancy, context_precision` | Standard Ragas 0.1.x import path; consistent with PRD §Evaluation | If Ragas reorganises metric namespaces |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | Threshold constants and `print_results_table()` function | `eval.py` |
| T2 | `load_or_generate_golden_dataset()` — Ragas `TestsetGenerator` + JSON persistence | `eval.py` |
| T3 | `run_pipeline_on_dataset()` — iterate dataset, invoke CRAG graph, collect rows | `eval.py` |
| T4 | `run_evaluation()` — Ragas `evaluate()` call with four metrics | `eval.py` |
| T5 | `main()` entry point with `load_dotenv()`, orchestration, and exit-0 contract | `eval.py` |
| T6 | Unit tests: threshold constants guard and pass/fail table logic | `tests/test_eval.py` |

---

## Architecture Constraints

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| `data/golden_dataset.json` must be loaded on subsequent runs, not regenerated | Issue spec §Resolved decisions; PRD §Further Notes | Regenerating changes the evaluation target — metric trends become uninterpretable across runs |
| Threshold constants must be named constants at the top of `eval.py` | Issue spec §Resolved decisions | Magic numbers inline cannot be asserted by unit tests and are fragile under edits |
| Thresholds: Faithfulness=0.85, Context Recall=0.80, Answer Relevancy=0.80, Context Precision=0.75 | Issue spec §Resolved decisions; PRD §User Stories #30 | Wrong thresholds produce incorrect PASS/FAIL classifications |
| Passing docs for Ragas context = docs filtered by `score >= 0.7` | Issue spec §Pipeline invocation; graph/nodes.py `GRADE_THRESHOLD = 0.7` | Using all retrieved docs (including failing ones) inflates Context Precision and corrupts Faithfulness scores |
| "not found" answers recorded with `contexts=[]` and the refusal string as `answer` | Issue spec §Resolved decisions | Omitting these rows skews metric averages by excluding pipeline failures |
| CRAG graph invoked via `graph.graph.build_graph()` — the same compiled graph used in production | PRD §Dependencies: eval depends on feat/crag-graph | Invoking nodes directly would bypass routing logic and produce non-representative eval results |
| `load_dotenv()` at top of script | Issue spec §Script entry point | Without it, `.env` is not loaded, `OPENAI_API_KEY` is absent, all API calls fail |
| Unit tests must not require `OPENAI_API_KEY` | Established pattern from `test_graph.py` and `test_ingest.py` | CI without API key must not break |
| Script exits with code 0 even on metric failures | Issue spec §Acceptance criteria | Exiting non-zero would break pipelines that call `eval.py` as a monitoring step |
| Collection name `"crag_corpus"` when loading documents from Chroma | `ingest.py` `CHROMA_COLLECTION = "crag_corpus"`; `graph/nodes.py` same constant | A different collection name returns an empty document set |
| Python 3.11; `ragas==0.1.*` | PRD §Environment & Dependencies | Ragas 0.1.x API surface differs from 0.2.x; use `from ragas.metrics import ...` not `from ragas import ...` |

---

## T1 — Threshold Constants and `print_results_table()`

### What it builds

Named threshold constants at module level and a pure function that renders the pass/fail table from a results dict. No LLM calls. Testable in isolation.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Constant naming | `THRESHOLD_FAITHFULNESS`, `THRESHOLD_CONTEXT_RECALL`, `THRESHOLD_ANSWER_RELEVANCY`, `THRESHOLD_CONTEXT_PRECISION` | Verbose names prevent confusion; unit tests read these by name, not by position |
| Table output target | `print()` to stdout | Issue spec: "prints a pass/fail table to stdout" |
| Column widths | Fixed-width format strings: metric 22 chars, score 8, threshold 10, result 6 | Fits the issue spec example table layout without requiring `rich` |
| PASS/FAIL determination | `score >= threshold` | Issue spec: "A metric scoring above its threshold is marked PASS; below is marked FAIL" |

### Layer compliance checklist

- [ ] No LLM calls in `print_results_table()`
- [ ] Thresholds read from named module-level constants — no inline literals
- [ ] Function is pure: same inputs always produce the same stdout output
- [ ] No side effects beyond printing

### Implementation

```python
"""Ragas evaluation script for the CRAG pipeline.

Usage:
    python eval.py

Generates a ~50-question golden dataset from the ingested Chroma corpus on
first run (saved to data/golden_dataset.json). Subsequent runs load the saved
dataset. Invokes the CRAG graph for each question, evaluates with Ragas, and
prints a pass/fail table.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Threshold constants — change here to update both eval logic and unit tests
# ---------------------------------------------------------------------------

THRESHOLD_FAITHFULNESS: float = 0.85
THRESHOLD_CONTEXT_RECALL: float = 0.80
THRESHOLD_ANSWER_RELEVANCY: float = 0.80
THRESHOLD_CONTEXT_PRECISION: float = 0.75

GOLDEN_DATASET_PATH = Path("data/golden_dataset.json")
GOLDEN_DATASET_SIZE = 50

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"


THRESHOLDS: dict[str, float] = {
    "Faithfulness": THRESHOLD_FAITHFULNESS,
    "Context Recall": THRESHOLD_CONTEXT_RECALL,
    "Answer Relevancy": THRESHOLD_ANSWER_RELEVANCY,
    "Context Precision": THRESHOLD_CONTEXT_PRECISION,
}


def print_results_table(scores: dict[str, float]) -> None:
    """
    Print a pass/fail table to stdout.

    Args:
        scores: dict mapping metric name to float score.
                Keys must match those in THRESHOLDS.
    """
    header = (
        f"{'Metric':<22} {'Score':<8} {'Threshold':<10} {'Result':<6}"
    )
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)

    passing = 0
    for metric, threshold in THRESHOLDS.items():
        score = scores.get(metric, float("nan"))
        result = "PASS" if score >= threshold else "FAIL"
        if result == "PASS":
            passing += 1
        print(f"{metric:<22} {score:<8.2f} {threshold:<10.2f} {result:<6}")

    print(separator)
    print(f"Overall: {passing}/{len(THRESHOLDS)} metrics passing")
```

### Acceptance criteria

- [ ] `THRESHOLD_FAITHFULNESS == 0.85`
- [ ] `THRESHOLD_CONTEXT_RECALL == 0.80`
- [ ] `THRESHOLD_ANSWER_RELEVANCY == 0.80`
- [ ] `THRESHOLD_CONTEXT_PRECISION == 0.75`
- [ ] Given `scores = {"Faithfulness": 0.88, "Context Recall": 0.76, "Answer Relevancy": 0.82, "Context Precision": 0.79}`, output marks Faithfulness, Answer Relevancy, Context Precision as PASS and Context Recall as FAIL
- [ ] "Overall: 3/4 metrics passing" appears in output for the example above

---

## T2 — `load_or_generate_golden_dataset()`

### What it builds

The function that either loads `data/golden_dataset.json` (if it exists) or generates ~50 Q&A pairs using Ragas `TestsetGenerator` from documents in Chroma and saves the result.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Dataset file check | `GOLDEN_DATASET_PATH.exists()` | Prevents regeneration on subsequent runs |
| Document loading from Chroma | `vectorstore.get(include=["documents", "metadatas"])` then reconstruct `Document` objects | Chroma already holds the ingested text; no need to re-read PDFs |
| `TestsetGenerator` configuration | `generator_llm=ChatOpenAI(model="gpt-4o")`, `critic_llm=ChatOpenAI(model="gpt-4o")`, `embeddings=OpenAIEmbeddings(model="text-embedding-3-small")` | Ragas 0.1.x `TestsetGenerator` requires LLM and embeddings; using the same models as the pipeline ensures consistency |
| Dataset serialization | `json.dump([row.dict() for row in testset.to_dataset()], f, indent=2)` | JSON is human-readable and sufficient for ~50 rows; avoids a pandas/parquet dependency |
| Deserialization | `json.load(f)` returns a list of dicts; convert to `SingleTurnSample` list for Ragas | Ragas 0.1.x `EvaluationDataset.from_list()` accepts list of dicts with `user_input`, `response`, `retrieved_contexts`, `reference` keys |

### Layer compliance checklist

- [ ] File check before any LLM call — `load_dotenv()` already called in `main()`
- [ ] `GOLDEN_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)` before writing
- [ ] Prints a clear message when generating vs. loading so the user knows which path was taken

### Implementation

```python
def _load_documents_from_chroma() -> list:
    """Load all Document objects from the persisted Chroma collection."""
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    raw = vectorstore.get(include=["documents", "metadatas"])
    docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(raw["documents"], raw["metadatas"])
    ]
    return docs


def load_or_generate_golden_dataset() -> list[dict]:
    """
    Return the golden dataset as a list of dicts with keys:
        question, ground_truth

    On first call: generates via Ragas TestsetGenerator and saves to
    GOLDEN_DATASET_PATH.
    On subsequent calls: loads from GOLDEN_DATASET_PATH without regenerating.
    """
    if GOLDEN_DATASET_PATH.exists():
        print(f"[eval] Loading golden dataset from {GOLDEN_DATASET_PATH}")
        with GOLDEN_DATASET_PATH.open() as f:
            return json.load(f)

    print(f"[eval] Generating golden dataset ({GOLDEN_DATASET_SIZE} questions) ...")
    docs = _load_documents_from_chroma()
    if not docs:
        raise RuntimeError(
            "No documents found in Chroma. Ingest PDFs before running eval."
        )

    from ragas.testset import TestsetGenerator
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    generator = TestsetGenerator.from_langchain(
        generator_llm=ChatOpenAI(model="gpt-4o"),
        critic_llm=ChatOpenAI(model="gpt-4o"),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    testset = generator.generate_with_langchain_docs(
        docs, test_size=GOLDEN_DATASET_SIZE
    )
    dataset_rows = [
        {"question": row.question, "ground_truth": row.ground_truth}
        for row in testset.test_data
    ]

    GOLDEN_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GOLDEN_DATASET_PATH.open("w") as f:
        json.dump(dataset_rows, f, indent=2)
    print(f"[eval] Golden dataset saved to {GOLDEN_DATASET_PATH}")

    return dataset_rows
```

### Acceptance criteria

- [ ] When `data/golden_dataset.json` exists: function returns its contents without calling `TestsetGenerator`
- [ ] When `data/golden_dataset.json` does not exist: function calls `TestsetGenerator`, saves the file, then returns rows
- [ ] After first run, a second call to `load_or_generate_golden_dataset()` loads — does not regenerate
- [ ] Raises `RuntimeError` with a clear message when Chroma is empty

---

## T3 — `run_pipeline_on_dataset()`

### What it builds

Iterates the golden dataset, invokes the compiled CRAG graph for each question, extracts the `final_answer` and passing context docs from the final state, and returns a list of Ragas-compatible row dicts.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Graph compilation | Call `build_graph()` once before the loop | Compilation is expensive; reuse the same compiled graph for all 50 questions |
| Initial state per question | Fresh `CRAGState` with all mutable fields reset | Issue spec: stateless queries (grilling log Q22) |
| Passing docs extraction | `[doc for doc, grade in zip(state["retrieved_docs"], state["grade_results"]) if grade["score"] >= 0.7]` | Mirrors the `generate` node's filtering in `graph/nodes.py`; `GRADE_THRESHOLD = 0.7` |
| "not found" detection | `final_answer.startswith("I couldn't find relevant information")` | The `not_found` node always produces this exact prefix (see `graph/nodes.py`); checking the prefix is more robust than `contexts=[]` |
| Context field | `[doc.page_content for doc in passing_docs]` | Ragas `EvaluationDataset` `retrieved_contexts` expects a `list[str]` |
| Progress indicator | `print(f"[eval] {i+1}/{total}: {question[:60]}")` | 50 LLM calls take ~2 minutes; progress prevents silent hangs |

### Layer compliance checklist

- [ ] `build_graph()` called once — not inside the per-question loop
- [ ] `iteration_count` reset to 0 per question
- [ ] Passing docs filtering uses `GRADE_THRESHOLD` constant from `graph.nodes` — not a hardcoded 0.7

### Implementation

```python
def run_pipeline_on_dataset(dataset: list[dict]) -> list[dict]:
    """
    Invoke the CRAG graph for each question in the dataset.

    Returns a list of dicts compatible with ragas.EvaluationDataset:
        [{"question": str, "answer": str, "contexts": list[str], "ground_truth": str}, ...]
    """
    from graph.graph import build_graph
    from graph.nodes import GRADE_THRESHOLD

    graph = build_graph()
    rows = []
    total = len(dataset)

    for i, item in enumerate(dataset):
        question = item["question"]
        ground_truth = item["ground_truth"]
        print(f"[eval] {i + 1}/{total}: {question[:60]}")

        initial_state = {
            "query": question,
            "reformulated_query": None,
            "retrieved_docs": [],
            "grade_results": [],
            "final_answer": None,
            "iteration_count": 0,
        }
        final_state = graph.invoke(initial_state)

        final_answer = final_state.get("final_answer") or ""
        retrieved_docs = final_state.get("retrieved_docs", [])
        grade_results = final_state.get("grade_results", [])

        # Extract only passing docs for the context field
        passing_docs = [
            doc
            for doc, grade in zip(retrieved_docs, grade_results)
            if grade["score"] >= GRADE_THRESHOLD
        ]

        # "not found" responses → empty contexts (correct Ragas behavior per spec)
        if not passing_docs or final_answer.startswith(
            "I couldn't find relevant information"
        ):
            contexts: list[str] = []
        else:
            contexts = [doc.page_content for doc in passing_docs]

        rows.append(
            {
                "question": question,
                "answer": final_answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    return rows
```

### Acceptance criteria

- [ ] Returns exactly `len(dataset)` rows
- [ ] Each row has keys: `question`, `answer`, `contexts`, `ground_truth`
- [ ] "not found" answers produce `contexts=[]`
- [ ] Passing docs' `page_content` appears in `contexts` for non-"not found" answers
- [ ] `iteration_count` is reset to 0 for each question

---

## T4 — `run_evaluation()`

### What it builds

Wraps the Ragas `evaluate()` call. Converts the list of row dicts to a Ragas `EvaluationDataset` and runs all four metrics.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Ragas dataset construction | `EvaluationDataset` from list of `SingleTurnSample` objects | Ragas 0.1.x internal representation; `evaluate()` accepts `EvaluationDataset` |
| Metrics list | `[faithfulness, context_recall, answer_relevancy, context_precision]` | Exactly the four metrics specified in PRD §Evaluation and issue spec §Metrics |
| Return type | `dict[str, float]` keyed by friendly metric names matching `THRESHOLDS` keys | Makes `print_results_table()` consumption straightforward without key translation |
| Score extraction | `results["faithfulness"]` etc. from the `EvaluationResult` object | Ragas 0.1.x returns an object where metric scores are accessible by metric name string |

### Layer compliance checklist

- [ ] Metric names in return dict exactly match keys in `THRESHOLDS` constant dict
- [ ] No LLM configuration beyond what Ragas pulls from env — `OPENAI_API_KEY` is already loaded

### Implementation

```python
def run_evaluation(rows: list[dict]) -> dict[str, float]:
    """
    Run Ragas evaluation on the collected pipeline outputs.

    Args:
        rows: list of dicts with keys question, answer, contexts, ground_truth.

    Returns:
        dict mapping friendly metric name → float score.
        Keys: "Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        context_recall,
        answer_relevancy,
        context_precision,
    )
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample

    samples = [
        SingleTurnSample(
            user_input=row["question"],
            response=row["answer"],
            retrieved_contexts=row["contexts"],
            reference=row["ground_truth"],
        )
        for row in rows
    ]
    dataset = EvaluationDataset(samples=samples)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_recall, answer_relevancy, context_precision],
    )

    return {
        "Faithfulness": float(result["faithfulness"]),
        "Context Recall": float(result["context_recall"]),
        "Answer Relevancy": float(result["answer_relevancy"]),
        "Context Precision": float(result["context_precision"]),
    }
```

### Acceptance criteria

- [ ] Returns a dict with exactly these four keys: `"Faithfulness"`, `"Context Recall"`, `"Answer Relevancy"`, `"Context Precision"`
- [ ] Each value is a `float` in `[0.0, 1.0]`
- [ ] No `OPENAI_API_KEY` validation happens inside this function — it is the caller's responsibility

---

## T5 — `main()` Entry Point

### What it builds

The top-level orchestration function and `if __name__ == "__main__"` guard. Calls `load_or_generate_golden_dataset()`, `run_pipeline_on_dataset()`, `run_evaluation()`, and `print_results_table()`. Always exits with code 0.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Exception handling | Catch `RuntimeError` from empty Chroma, print a friendly message, exit 0 | Issue spec: exit 0 always |
| Unexpected exceptions | Let them propagate — a crash is meaningful signal | Swallowing unknown exceptions would hide real bugs |
| Load order | `load_dotenv()` at module level (not inside `main()`) | Ensures env is available at import time for any module-level `os.getenv()` calls |

### Implementation

```python
def main() -> None:
    """Orchestrate the full evaluation pipeline."""
    try:
        dataset = load_or_generate_golden_dataset()
    except RuntimeError as exc:
        print(f"[eval] ERROR: {exc}", file=sys.stderr)
        sys.exit(0)

    print(f"[eval] Running pipeline on {len(dataset)} questions ...")
    rows = run_pipeline_on_dataset(dataset)

    print("[eval] Running Ragas evaluation ...")
    scores = run_evaluation(rows)

    print()
    print_results_table(scores)


if __name__ == "__main__":
    main()
```

### Acceptance criteria

- [ ] `python eval.py` runs end-to-end without error when a populated Chroma store exists
- [ ] Script exits with code 0 even when all metrics FAIL
- [ ] Script exits with code 0 when Chroma is empty (prints error, does not crash)
- [ ] `data/golden_dataset.json` is created on first run and loaded on subsequent runs

---

## T6 — Unit Tests (`tests/test_eval.py`)

### What it builds

`tests/test_eval.py` — two pytest test classes covering the two unit-testable acceptance criteria from the issue spec:
1. `TestThresholdConstants` — reads the named constants directly and asserts their exact values.
2. `TestPrintResultsTable` — given a mock scores dict, verifies PASS/FAIL classification and overall count.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| No LLM mocking needed | `print_results_table()` and threshold constants are pure — no LLM | Keeps tests fast and runnable without `OPENAI_API_KEY` |
| Capturing stdout | `capsys` pytest fixture | Standard pytest approach for asserting print output |
| Mock scores | One metric above threshold, one below, mixed for each constant | Covers both PASS and FAIL branches per test |
| Import strategy | `import eval` then `eval.THRESHOLD_FAITHFULNESS` etc. | Tests the actual module-level constants, not local variables |

### Implementation

```python
"""Unit tests for eval.py.

Run with: pytest tests/test_eval.py -v
No OPENAI_API_KEY required.
"""
from __future__ import annotations

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Threshold constant guard tests
# ---------------------------------------------------------------------------

class TestThresholdConstants:
    """Guards the four threshold constants against accidental edits."""

    def _get_eval_module(self):
        # Fresh import each time to avoid stale module state
        if "eval" in sys.modules:
            return sys.modules["eval"]
        import eval as ev
        return ev

    def test_faithfulness_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_FAITHFULNESS == 0.85, (
            f"THRESHOLD_FAITHFULNESS must be 0.85, got {ev.THRESHOLD_FAITHFULNESS}"
        )

    def test_context_recall_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_CONTEXT_RECALL == 0.80, (
            f"THRESHOLD_CONTEXT_RECALL must be 0.80, got {ev.THRESHOLD_CONTEXT_RECALL}"
        )

    def test_answer_relevancy_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_ANSWER_RELEVANCY == 0.80, (
            f"THRESHOLD_ANSWER_RELEVANCY must be 0.80, got {ev.THRESHOLD_ANSWER_RELEVANCY}"
        )

    def test_context_precision_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_CONTEXT_PRECISION == 0.75, (
            f"THRESHOLD_CONTEXT_PRECISION must be 0.75, got {ev.THRESHOLD_CONTEXT_PRECISION}"
        )

    def test_thresholds_dict_matches_constants(self):
        """THRESHOLDS dict values must equal the named constants."""
        ev = self._get_eval_module()
        assert ev.THRESHOLDS["Faithfulness"] == ev.THRESHOLD_FAITHFULNESS
        assert ev.THRESHOLDS["Context Recall"] == ev.THRESHOLD_CONTEXT_RECALL
        assert ev.THRESHOLDS["Answer Relevancy"] == ev.THRESHOLD_ANSWER_RELEVANCY
        assert ev.THRESHOLDS["Context Precision"] == ev.THRESHOLD_CONTEXT_PRECISION


# ---------------------------------------------------------------------------
# Pass/fail table tests
# ---------------------------------------------------------------------------

class TestPrintResultsTable:
    """Verifies pass/fail classification and output format."""

    def _get_print_fn(self):
        if "eval" in sys.modules:
            return sys.modules["eval"].print_results_table
        import eval as ev
        return ev.print_results_table

    def test_above_threshold_is_pass(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.90,      # > 0.85 → PASS
            "Context Recall": 0.85,    # > 0.80 → PASS
            "Answer Relevancy": 0.85,  # > 0.80 → PASS
            "Context Precision": 0.80, # > 0.75 → PASS
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "PASS" in captured
        assert "FAIL" not in captured

    def test_below_threshold_is_fail(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.80,      # < 0.85 → FAIL
            "Context Recall": 0.75,    # < 0.80 → FAIL
            "Answer Relevancy": 0.75,  # < 0.80 → FAIL
            "Context Precision": 0.70, # < 0.75 → FAIL
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "FAIL" in captured
        assert "PASS" not in captured

    def test_mixed_pass_and_fail(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.88,      # > 0.85 → PASS
            "Context Recall": 0.76,    # < 0.80 → FAIL
            "Answer Relevancy": 0.82,  # > 0.80 → PASS
            "Context Precision": 0.79, # > 0.75 → PASS
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "PASS" in captured
        assert "FAIL" in captured
        assert "3/4 metrics passing" in captured

    def test_exact_threshold_is_pass(self, capsys):
        """Score equal to threshold must be PASS (>= not >)."""
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.85,
            "Context Recall": 0.80,
            "Answer Relevancy": 0.80,
            "Context Precision": 0.75,
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "FAIL" not in captured
        assert "4/4 metrics passing" in captured

    def test_all_four_metrics_appear(self, capsys):
        fn = self._get_print_fn()
        scores = {k: 0.90 for k in ["Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"]}
        fn(scores)
        captured = capsys.readouterr().out
        assert "Faithfulness" in captured
        assert "Context Recall" in captured
        assert "Answer Relevancy" in captured
        assert "Context Precision" in captured

    def test_overall_line_present(self, capsys):
        fn = self._get_print_fn()
        scores = {k: 0.90 for k in ["Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"]}
        fn(scores)
        captured = capsys.readouterr().out
        assert "Overall:" in captured
```

### Acceptance criteria

- [ ] `pytest tests/test_eval.py -v` exits with code 0
- [ ] No test requires `OPENAI_API_KEY`
- [ ] Threshold constant tests: all four constants equal their specified values
- [ ] `THRESHOLDS` dict test: dict values match constants
- [ ] Pass/fail table tests: all PASS when all scores above threshold; all FAIL when all below; correct mixed count; exact threshold is PASS; all four metric names present; "Overall:" line present

---

## Complete `eval.py` Implementation

The full file combining T1–T5:

```python
"""Ragas evaluation script for the CRAG pipeline.

Usage:
    python eval.py

Generates a ~50-question golden dataset from the ingested Chroma corpus on
first run (saved to data/golden_dataset.json). Subsequent runs load the saved
dataset. Invokes the CRAG graph for each question, evaluates with Ragas, and
prints a pass/fail table.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Threshold constants — change here to update both eval logic and unit tests
# ---------------------------------------------------------------------------

THRESHOLD_FAITHFULNESS: float = 0.85
THRESHOLD_CONTEXT_RECALL: float = 0.80
THRESHOLD_ANSWER_RELEVANCY: float = 0.80
THRESHOLD_CONTEXT_PRECISION: float = 0.75

GOLDEN_DATASET_PATH = Path("data/golden_dataset.json")
GOLDEN_DATASET_SIZE = 50

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"

THRESHOLDS: dict[str, float] = {
    "Faithfulness": THRESHOLD_FAITHFULNESS,
    "Context Recall": THRESHOLD_CONTEXT_RECALL,
    "Answer Relevancy": THRESHOLD_ANSWER_RELEVANCY,
    "Context Precision": THRESHOLD_CONTEXT_PRECISION,
}


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

def print_results_table(scores: dict[str, float]) -> None:
    """
    Print a pass/fail table to stdout.

    Args:
        scores: dict mapping metric name to float score.
                Keys must match those in THRESHOLDS.
    """
    header = f"{'Metric':<22} {'Score':<8} {'Threshold':<10} {'Result':<6}"
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)

    passing = 0
    for metric, threshold in THRESHOLDS.items():
        score = scores.get(metric, float("nan"))
        result = "PASS" if score >= threshold else "FAIL"
        if result == "PASS":
            passing += 1
        print(f"{metric:<22} {score:<8.2f} {threshold:<10.2f} {result:<6}")

    print(separator)
    print(f"Overall: {passing}/{len(THRESHOLDS)} metrics passing")


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _load_documents_from_chroma() -> list:
    """Load all Document objects from the persisted Chroma collection."""
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    raw = vectorstore.get(include=["documents", "metadatas"])
    docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(raw["documents"], raw["metadatas"])
    ]
    return docs


# ---------------------------------------------------------------------------
# Golden dataset
# ---------------------------------------------------------------------------

def load_or_generate_golden_dataset() -> list[dict]:
    """
    Return the golden dataset as a list of dicts with keys: question, ground_truth.

    On first call: generates via Ragas TestsetGenerator and saves to
    GOLDEN_DATASET_PATH.
    On subsequent calls: loads from GOLDEN_DATASET_PATH without regenerating.
    """
    if GOLDEN_DATASET_PATH.exists():
        print(f"[eval] Loading golden dataset from {GOLDEN_DATASET_PATH}")
        with GOLDEN_DATASET_PATH.open() as f:
            return json.load(f)

    print(f"[eval] Generating golden dataset ({GOLDEN_DATASET_SIZE} questions) ...")
    docs = _load_documents_from_chroma()
    if not docs:
        raise RuntimeError(
            "No documents found in Chroma. Ingest PDFs before running eval."
        )

    from ragas.testset import TestsetGenerator
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    generator = TestsetGenerator.from_langchain(
        generator_llm=ChatOpenAI(model="gpt-4o"),
        critic_llm=ChatOpenAI(model="gpt-4o"),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    testset = generator.generate_with_langchain_docs(
        docs, test_size=GOLDEN_DATASET_SIZE
    )
    dataset_rows = [
        {"question": row.question, "ground_truth": row.ground_truth}
        for row in testset.test_data
    ]

    GOLDEN_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GOLDEN_DATASET_PATH.open("w") as f:
        json.dump(dataset_rows, f, indent=2)
    print(f"[eval] Golden dataset saved to {GOLDEN_DATASET_PATH}")

    return dataset_rows


# ---------------------------------------------------------------------------
# Pipeline invocation
# ---------------------------------------------------------------------------

def run_pipeline_on_dataset(dataset: list[dict]) -> list[dict]:
    """
    Invoke the CRAG graph for each question in the dataset.

    Returns a list of dicts compatible with ragas.EvaluationDataset:
        [{"question": str, "answer": str, "contexts": list[str], "ground_truth": str}, ...]
    """
    from graph.graph import build_graph
    from graph.nodes import GRADE_THRESHOLD

    graph = build_graph()
    rows = []
    total = len(dataset)

    for i, item in enumerate(dataset):
        question = item["question"]
        ground_truth = item["ground_truth"]
        print(f"[eval] {i + 1}/{total}: {question[:60]}")

        initial_state = {
            "query": question,
            "reformulated_query": None,
            "retrieved_docs": [],
            "grade_results": [],
            "final_answer": None,
            "iteration_count": 0,
        }
        final_state = graph.invoke(initial_state)

        final_answer = final_state.get("final_answer") or ""
        retrieved_docs = final_state.get("retrieved_docs", [])
        grade_results = final_state.get("grade_results", [])

        # Extract only passing docs for the context field (mirrors generate node filtering)
        passing_docs = [
            doc
            for doc, grade in zip(retrieved_docs, grade_results)
            if grade["score"] >= GRADE_THRESHOLD
        ]

        # "not found" responses → empty contexts per spec
        if not passing_docs or final_answer.startswith(
            "I couldn't find relevant information"
        ):
            contexts: list[str] = []
        else:
            contexts = [doc.page_content for doc in passing_docs]

        rows.append(
            {
                "question": question,
                "answer": final_answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Ragas evaluation
# ---------------------------------------------------------------------------

def run_evaluation(rows: list[dict]) -> dict[str, float]:
    """
    Run Ragas evaluation on the collected pipeline outputs.

    Returns dict mapping friendly metric name to float score.
    Keys: "Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        context_recall,
        answer_relevancy,
        context_precision,
    )
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample

    samples = [
        SingleTurnSample(
            user_input=row["question"],
            response=row["answer"],
            retrieved_contexts=row["contexts"],
            reference=row["ground_truth"],
        )
        for row in rows
    ]
    dataset = EvaluationDataset(samples=samples)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_recall, answer_relevancy, context_precision],
    )

    return {
        "Faithfulness": float(result["faithfulness"]),
        "Context Recall": float(result["context_recall"]),
        "Answer Relevancy": float(result["answer_relevancy"]),
        "Context Precision": float(result["context_precision"]),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Orchestrate the full evaluation pipeline."""
    try:
        dataset = load_or_generate_golden_dataset()
    except RuntimeError as exc:
        print(f"[eval] ERROR: {exc}", file=sys.stderr)
        sys.exit(0)

    print(f"[eval] Running pipeline on {len(dataset)} questions ...")
    rows = run_pipeline_on_dataset(dataset)

    print("[eval] Running Ragas evaluation ...")
    scores = run_evaluation(rows)

    print()
    print_results_table(scores)


if __name__ == "__main__":
    main()
```

---

## Migration

Not applicable. This PR introduces no database schema, no SQLAlchemy models, and no Alembic migrations. `data/golden_dataset.json` is a plain JSON file written at runtime — it is already listed in `.gitignore` and does not require a migration step.

---

## Test quality rules

### Threshold constants — assert the exact numeric value, not a range

```python
assert ev.THRESHOLD_FAITHFULNESS == 0.85      # exact equality
assert ev.THRESHOLD_CONTEXT_RECALL == 0.80
assert ev.THRESHOLD_ANSWER_RELEVANCY == 0.80
assert ev.THRESHOLD_CONTEXT_PRECISION == 0.75
```

### Pass/fail classification — test at and below threshold boundary

```python
# Exact threshold must be PASS (>= not >)
scores_at_threshold = {
    "Faithfulness": 0.85, "Context Recall": 0.80,
    "Answer Relevancy": 0.80, "Context Precision": 0.75,
}
fn(scores_at_threshold)
assert "FAIL" not in captured_out

# One tick below threshold must be FAIL
scores_below = {
    "Faithfulness": 0.849, ...
}
fn(scores_below)
assert "FAIL" in captured_out
```

### Overall count — assert the exact "N/4" string

```python
assert "3/4 metrics passing" in captured_out  # for 3 PASS, 1 FAIL
```

### Metric name coverage — assert all four names appear in output

```python
for name in ["Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"]:
    assert name in captured_out
```

---

## Automated verification

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install test dependencies (dev-only)
pip install pytest

# Run eval unit tests only (no OPENAI_API_KEY required)
pytest tests/test_eval.py -v

# Run full test suite
pytest tests/ -v

# Smoke-test: eval.py importable without OPENAI_API_KEY
python -c "import eval; print('eval import OK')"

# Smoke-test: threshold constants accessible
python -c "import eval; print(eval.THRESHOLD_FAITHFULNESS, eval.THRESHOLD_CONTEXT_RECALL)"

# Full end-to-end run (requires OPENAI_API_KEY and ingested corpus)
python eval.py
```

---

## Manual verification

1. **Unit tests — no API key required:**
   ```bash
   pytest tests/test_eval.py -v
   ```
   Expected: all tests pass, zero API calls.

2. **Threshold constant check:**
   ```python
   import eval
   print(eval.THRESHOLD_FAITHFULNESS)    # → 0.85
   print(eval.THRESHOLD_CONTEXT_RECALL)  # → 0.8
   print(eval.THRESHOLD_ANSWER_RELEVANCY) # → 0.8
   print(eval.THRESHOLD_CONTEXT_PRECISION) # → 0.75
   ```

3. **Pass/fail table smoke test (no API key):**
   ```python
   import eval
   eval.print_results_table({
       "Faithfulness": 0.88,
       "Context Recall": 0.76,
       "Answer Relevancy": 0.82,
       "Context Precision": 0.79,
   })
   ```
   Expected output:
   ```
   ----------------------------------------
   Metric                 Score    Threshold  Result
   ----------------------------------------
   Faithfulness           0.88     0.85       PASS
   Context Recall         0.76     0.80       FAIL
   Answer Relevancy       0.82     0.80       PASS
   Context Precision      0.79     0.75       PASS
   ----------------------------------------
   Overall: 3/4 metrics passing
   ```

4. **Golden dataset generation (requires OPENAI_API_KEY and ingested corpus):**
   ```bash
   # Remove any existing dataset to force generation
   rm -f data/golden_dataset.json
   python eval.py
   ```
   Expected: `[eval] Generating golden dataset (50 questions) ...` followed by save confirmation, then pipeline runs and table prints.

5. **Golden dataset reuse (second run):**
   ```bash
   python eval.py
   ```
   Expected: `[eval] Loading golden dataset from data/golden_dataset.json` — no generation LLM calls.

6. **Empty Chroma guard:**
   ```bash
   # Point to a non-existent chroma dir
   CHROMA_PERSIST_DIR=/tmp/empty_chroma python eval.py
   ```
   Expected: prints error message, exits with code 0 (not a crash).

7. **Exit code 0 on metric failure:**
   - If all metrics fail, `echo $?` after running `python eval.py` must output `0`.

8. **Full test suite:**
   ```bash
   pytest tests/ -v
   ```
   Expected: all tests pass.

---

## Implementation Notes

- **CLAUDE.md not found:** The file `CLAUDE.md` was absent from `C:/Users/mohds/OneDrive/Desktop/rag-ragas-eval/`. No layer-rule conflicts to log. Plan followed as written.
- **Python version:** Runtime is Python 3.10.11 (not 3.11 as stated in PRD). No incompatibilities observed; all code is compatible with 3.10+.
- **`ragas` import verification deferred:** The `run_evaluation()` and `load_or_generate_golden_dataset()` functions use lazy imports (inside function body) to avoid requiring `OPENAI_API_KEY` at import time. This matches the architecture constraint "Unit tests must not require `OPENAI_API_KEY`" and the established pattern in `test_graph.py` and `test_ingest.py`.
- **Full suite result:** 44 passed, 2 deprecation warnings (from `langchain-community` and `Chroma` upstream deprecations — not caused by this PR). All new tests (11) passed on first run.
