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

        # "not found" responses -> empty contexts per spec
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
