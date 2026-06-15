# PR3 — feat: CRAG LangGraph nodes, routing, and assembly

**Branch:** `feat/crag-graph`
**PR ID:** PR-3
**Depends on:** PR-1 (chore/project-scaffold), PR-2 (feat/pdf-ingestion)

---

## What This PR Does

This PR replaces the stub files `graph/nodes.py` and `graph/graph.py` with the full CRAG state-machine implementation. It wires five LangGraph node functions (`retrieve`, `grade_documents`, `reformulate_query`, `generate`, `not_found`) and a pure routing function (`route_after_grading`) into a compiled graph that accepts a query, routes it through retrieval and relevance grading, conditionally reformulates the query up to two times, and terminates with either a grounded generated answer or a structured "not found" refusal. It also delivers `tests/test_graph.py`, which exercises all routing branches and the `not_found` output contract without requiring a real OpenAI API key.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | Chroma retriever init inside `retrieve` node vs. module-level | Module-level `_get_retriever()` factory cached at call time | Avoids constructing a new Chroma client on every node invocation; mirrors the `_get_vectorstore()` pattern in `ingest.py` | If the graph is invoked concurrently across threads |
| 2 | `GradeOutput` Pydantic model location | Defined in `graph/nodes.py` alongside the node that uses it | It is a private implementation detail of the grader node; not part of the public state schema in `graph/state.py` | If other modules need to parse grader output directly |
| 3 | `doc_id` field in `GradeResult` | Use `Document.metadata.get("source", "") + "_" + str(index)` as a synthetic ID | `langchain_core.documents.Document` has no `.id` attribute by default; a deterministic synthetic ID is sufficient for matching grade results to docs | If LangChain adds a stable doc ID field |
| 4 | Generator prompt format | Simple f-string template with context chunks joined by `"\n\n"` and the question appended | PRD does not specify a prompt template for generation; minimal template is conservative and avoids prompt-engineering assumptions | If RAG eval scores indicate prompt needs tuning |
| 5 | Reformulation prompt | Single-turn prompt: `"Original query: {query}\nReason the documents were not relevant: {reason}\nReformulate the query to better retrieve relevant documents."` | PRD specifies only that the prompt contains the original query and the highest-scoring failed reason; exact wording is unspecified | If reformulation produces semantically identical queries and RAG metrics suffer |
| 6 | `ChatOpenAI` import source | `langchain_openai.ChatOpenAI` | Consistent with `ingest.py` which uses `langchain_openai.OpenAIEmbeddings`; avoids raw `openai` SDK which would bypass Phoenix instrumentation | Never — PRD explicitly requires `langchain-openai` |
| 7 | `with_structured_output` Pydantic schema location | Inline `GradeOutput(BaseModel)` in `nodes.py` | LangChain `.with_structured_output()` requires a Pydantic `BaseModel` or JSON schema dict; TypedDict is not supported directly | If LangGraph adds native TypedDict support for structured output |
| 8 | Test mock strategy for LLM calls | `unittest.mock.patch` on the `ChatOpenAI` constructor and `.with_structured_output()` return value | Same pattern used in `test_ingest.py` for `OpenAIEmbeddings`; no `OPENAI_API_KEY` needed | If integration tests are added separately |
| 9 | Test mock strategy for Chroma retriever | Patch `graph.nodes._get_retriever` to return a `MagicMock` with `.similarity_search()` returning a controlled `list[Document]` | Isolates node logic from vector store; consistent with how `test_ingest.py` patches `_get_vectorstore` | Never |
| 10 | `build_graph()` returns `CompiledGraph` type annotation | Use `-> Any` with a comment referencing `langgraph.graph.CompiledGraph` | `langgraph==0.2.x` does not export `CompiledGraph` as a public symbol consistently across patch versions; `Any` avoids import errors | When LangGraph stabilises its public type API |
| 11 | `langchain_text_splitters` vs `langchain.text_splitter` | Use `langchain_text_splitters` | PR2 implementation notes document that `langchain.text_splitter` is removed in installed langchain 0.3.x; same package context applies here | Never — confirmed in PR2 |
| 12 | `langchain_core.documents.Document` vs `langchain.schema.Document` | Use `langchain_core.documents.Document` | PR2 implementation notes document that `langchain.schema` is removed; `langchain_core` is canonical | Never — confirmed in PR2 |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | `GradeOutput` Pydantic model + `retrieve` node | `graph/nodes.py` |
| T2 | `grade_documents` node with structured output | `graph/nodes.py` |
| T3 | `reformulate_query` node | `graph/nodes.py` |
| T4 | `generate` node with score-filtered context | `graph/nodes.py` |
| T5 | `not_found` node with exact refusal string | `graph/nodes.py` |
| T6 | `route_after_grading` routing function | `graph/nodes.py` |
| T7 | `build_graph()` — graph assembly and compilation | `graph/graph.py` |
| T8 | Unit tests covering routing, `not_found`, `generate` filtering, `grade_documents` | `tests/test_graph.py` |

---

## Architecture Constraints

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| State is immutable between nodes — return partial dicts only | PRD §LangGraph State | Mutating `state` in-place causes LangGraph merge to produce stale or double-applied values |
| `grade_documents` must use `.with_structured_output()` with a Pydantic model | PRD §LangGraph Nodes | Without structured output, JSON parse failures on `gpt-4o-mini` responses are not retried automatically |
| Grader and reformulator use `gpt-4o-mini`; generator uses `gpt-4o` | PRD §LLM Assignment | Cost and quality contract — switching models breaks the pipeline's cost assumptions |
| Collection name must be `"crag_corpus"` | PRD §Ingestion Module, `ingest.py` | A different name creates a separate Chroma collection that is empty; retrieval returns nothing |
| `OPENAI_API_KEY` read from env via `python-dotenv` `load_dotenv()` | PRD §Environment | Without `load_dotenv()`, `.env` file is ignored and API calls fail |
| `route_after_grading` must be a pure function — no LLM calls | PRD §Graph Assembly | Impure routing would break LangGraph's conditional edge contract and make routing non-deterministic |
| Reformulation loop cap at `iteration_count < 2` | PRD §Relevance Grading Thresholds | Loop cap of `< 2` means at most 2 reformulations (iterations 0→1 and 1→2) before `not_found`; using `<= 2` would allow 3 reformulations |
| `generate` must filter docs to `score >= 0.7` before passing to LLM | PRD §LangGraph Nodes | Passing all docs defeats the CRAG grading step and reintroduces irrelevant context to the generator |
| `not_found` refusal string must include `"Best relevance score:"`, score rounded to 2 decimal places, and the reason verbatim | Issue spec §Acceptance criteria | UI and evaluation scripts pattern-match this exact string format |
| No Arize Phoenix instrumentation in this PR | Issue spec §Out of scope | Phoenix setup belongs to PR-4; adding it here creates an undeclared dependency on `arize-phoenix` being installed and configured |
| Unit tests must not require `OPENAI_API_KEY` | Issue spec §Acceptance criteria | CI without API key would break |
| Use `langchain_core.documents.Document` (not `langchain.schema.Document`) | PR2 implementation notes | `langchain.schema` removed in installed langchain 0.3.x |
| Use `langchain_openai.ChatOpenAI` (not raw `openai` SDK) | PRD §Observability | Raw SDK calls bypass LangChain instrumentation that Phoenix uses in PR-4 |

---

## T1 — `GradeOutput` Pydantic Model and `retrieve` Node

### What it builds

The `GradeOutput` Pydantic model that `.with_structured_output()` targets, and the `retrieve` node function. `retrieve` reads the active query from state, queries Chroma for the top-5 most similar documents, and returns the partial state dict `{"retrieved_docs": <list>}`.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| `GradeOutput` base class | `pydantic.BaseModel` | LangChain `.with_structured_output()` requires `BaseModel` or JSON schema dict |
| Field validation on `score` | `float` with `ge=0.0, le=1.0` | Bounds the LLM output; `.with_structured_output()` validates on parse |
| `retrieve` uses `reformulated_query` if set | `active_query = state.get("reformulated_query") or state["query"]` | `reformulated_query` is `None` on first pass; `or` short-circuits to original query |
| Top-k constant | `k=5` | PRD §LangGraph Nodes specifies top-5 |
| Retriever initialisation | Module-level `_get_retriever()` using same `CHROMA_PERSIST_DIR` and `CHROMA_COLLECTION` as `ingest.py` | Ensures the same collection is queried |

### Layer compliance checklist

- [ ] `retrieve` returns a dict — not a `CRAGState` object
- [ ] No mutation of the input `state` dict
- [ ] No LLM call in `retrieve`
- [ ] `CHROMA_PERSIST_DIR` and `CHROMA_COLLECTION` read from module-level constants (mirroring `ingest.py`)

### Implementation

```python
"""LangGraph node functions for the CRAG pipeline."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from pydantic import BaseModel, Field

from graph.state import CRAGState, GradeResult

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"
GRADE_THRESHOLD = 0.7
MAX_ITERATIONS = 2


class GradeOutput(BaseModel):
    """Structured output schema for the relevance grader LLM call."""

    relevant: bool = Field(description="Whether the document is relevant to the query")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score between 0.0 and 1.0")
    reason: str = Field(description="Brief explanation of the relevance decision")


def _get_retriever():
    """Return a Chroma retriever for the crag_corpus collection."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    return vectorstore


def retrieve(state: CRAGState) -> dict:
    """
    Retrieve the top-5 most similar documents for the active query.

    Uses reformulated_query if set, otherwise falls back to the original query.
    Returns: {"retrieved_docs": list[Document]}
    """
    active_query = state.get("reformulated_query") or state["query"]
    vectorstore = _get_retriever()
    docs = vectorstore.similarity_search(active_query, k=5)
    return {"retrieved_docs": docs}
```

### Acceptance criteria

- [ ] `retrieve` returns `{"retrieved_docs": <list>}` — no other keys
- [ ] When `reformulated_query` is `None`, `retrieve` uses `state["query"]`
- [ ] When `reformulated_query` is a non-empty string, `retrieve` uses that string
- [ ] `len(retrieved_docs) <= 5` (Chroma returns at most k=5)

---

## T2 — `grade_documents` Node

### What it builds

The `grade_documents` node, which calls `gpt-4o-mini` once per retrieved document via `.with_structured_output(GradeOutput)`, and assembles the results into a list of `GradeResult` TypedDicts.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| One LLM call per document | Sequential `for` loop | PRD §LangGraph Nodes specifies individual grading per doc; batching would require a different prompt design |
| `relevant` field value | `score >= GRADE_THRESHOLD` computed in Python, not trusted from LLM | The LLM's `relevant` bool might be inconsistent with its own `score`; Python recompute is authoritative |
| `doc_id` synthetic key | `f"{doc.metadata.get('source', 'unknown')}_{i}"` where `i` is the index in `retrieved_docs` | Documents have no stable ID; source+index is deterministic for the lifetime of one pipeline invocation |
| Grader LLM | `ChatOpenAI(model="gpt-4o-mini")` | PRD §LLM Assignment |
| Grading prompt | System prompt describing the task + human message with `doc.page_content` and the active query | Minimal prompt; no chain-of-thought to keep token cost low |

### Implementation

```python
def grade_documents(state: CRAGState) -> dict:
    """
    Grade each retrieved document for relevance to the active query.

    Calls gpt-4o-mini once per document via structured output.
    Sets relevant=True iff score >= 0.7 (Python-computed, not trusted from LLM).
    Returns: {"grade_results": list[GradeResult]}
    """
    active_query = state.get("reformulated_query") or state["query"]
    docs: list[Document] = state["retrieved_docs"]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    grader = llm.with_structured_output(GradeOutput)

    grade_results: list[GradeResult] = []
    for i, doc in enumerate(docs):
        prompt = (
            f"You are a relevance grader. Given the following document and query, "
            f"rate the document's relevance on a scale of 0.0 to 1.0.\n\n"
            f"Query: {active_query}\n\n"
            f"Document: {doc.page_content}"
        )
        output: GradeOutput = grader.invoke(prompt)
        grade_results.append(
            GradeResult(
                doc_id=f"{doc.metadata.get('source', 'unknown')}_{i}",
                score=output.score,
                relevant=output.score >= GRADE_THRESHOLD,
                reason=output.reason,
            )
        )

    return {"grade_results": grade_results}
```

### Acceptance criteria

- [ ] `grade_results` has exactly one entry per document in `retrieved_docs`
- [ ] Each `GradeResult` has `relevant=True` iff `score >= 0.7` (Python-computed)
- [ ] Node returns only `{"grade_results": ...}` — no other keys
- [ ] Mock test: given a mock LLM returning `score=0.8`, `grade_results[0]["relevant"]` is `True`
- [ ] Mock test: given a mock LLM returning `score=0.5`, `grade_results[0]["relevant"]` is `False`

---

## T3 — `reformulate_query` Node

### What it builds

The `reformulate_query` node, which builds a prompt from the original query and the highest-scoring failed `GradeResult.reason`, calls `gpt-4o-mini` for a new query string, and increments `iteration_count`.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Source of `reason` for reformulation prompt | `GradeResult` with highest `score` among all failed docs | PRD §LangGraph Nodes: "the highest-scoring failed reason field" — uses the most informative failure signal |
| Fallback when `grade_results` is empty | Use empty string for reason | Defensive; should not occur in normal flow since `grade_documents` always runs before this node |
| Reformulation output parsing | Plain string from `llm.invoke()` → `.content` | No structured output needed; a single string is sufficient |
| `iteration_count` increment | `state["iteration_count"] + 1` in the returned dict | PRD §LangGraph Nodes; LangGraph merges this into state |

### Implementation

```python
def reformulate_query(state: CRAGState) -> dict:
    """
    Reformulate the query using the reason from the best-scoring failed GradeResult.

    Increments iteration_count.
    Returns: {"reformulated_query": str, "iteration_count": int}
    """
    original_query = state["query"]
    grade_results: list[GradeResult] = state.get("grade_results", [])

    # Find the reason from the highest-scoring (but still failing) grade result
    if grade_results:
        best_failed = max(grade_results, key=lambda r: r["score"])
        reason = best_failed["reason"]
    else:
        reason = ""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = (
        f"Original query: {original_query}\n"
        f"Reason the documents were not relevant: {reason}\n"
        f"Reformulate the query to better retrieve relevant documents. "
        f"Return only the reformulated query string, nothing else."
    )
    response = llm.invoke(prompt)
    new_query = response.content.strip()

    return {
        "reformulated_query": new_query,
        "iteration_count": state["iteration_count"] + 1,
    }
```

### Acceptance criteria

- [ ] Returns `{"reformulated_query": <non-empty string>, "iteration_count": <previous + 1>}`
- [ ] `iteration_count` in the returned dict equals `state["iteration_count"] + 1`
- [ ] Does not modify any other state key
- [ ] Uses `state["query"]` (original) for the prompt, not `state.get("reformulated_query")`

---

## T4 — `generate` Node

### What it builds

The `generate` node, which filters `retrieved_docs` to only those whose corresponding `GradeResult.score >= 0.7`, formats them as context, and calls `gpt-4o` to produce the final answer.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Doc-to-grade matching | By list index — `grade_results[i]` corresponds to `retrieved_docs[i]` | `grade_documents` iterates `retrieved_docs` in order and appends results in the same order; index alignment is guaranteed |
| Context format | `"\n\n".join(doc.page_content for doc in passing_docs)` | Simple, token-efficient; no XML or markdown wrapper needed for basic RAG |
| Generator prompt | System message describing the task + human message with context and question | Standard RAG prompt pattern; conservative choice |
| Generator LLM | `ChatOpenAI(model="gpt-4o", temperature=0)` | PRD §LLM Assignment |
| Edge case: all docs filtered out | This should not occur — `route_after_grading` only routes to `generate` when at least one doc passes | Defensive guard: if `passing_docs` is empty despite routing, return `"Unable to generate answer: no relevant context."` |

### Implementation

```python
def generate(state: CRAGState) -> dict:
    """
    Generate a final answer using only documents that scored >= 0.7.

    Returns: {"final_answer": str}
    """
    docs: list[Document] = state["retrieved_docs"]
    grade_results: list[GradeResult] = state["grade_results"]

    # Filter docs to those with passing grade scores (index-aligned with grade_results)
    passing_docs = [
        doc for doc, grade in zip(docs, grade_results)
        if grade["score"] >= GRADE_THRESHOLD
    ]

    if not passing_docs:
        # Defensive guard — routing should prevent this
        return {"final_answer": "Unable to generate answer: no relevant context."}

    context = "\n\n".join(doc.page_content for doc in passing_docs)
    active_query = state.get("reformulated_query") or state["query"]

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = (
        f"You are a helpful assistant. Answer the question using only the provided context. "
        f"If the context does not contain the answer, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {active_query}"
    )
    response = llm.invoke(prompt)
    return {"final_answer": response.content.strip()}
```

### Acceptance criteria

- [ ] Only docs with `grade_results[i]["score"] >= 0.7` are included in context (verified by mock)
- [ ] Docs with `score < 0.7` are excluded even if they exist in `retrieved_docs`
- [ ] Returns `{"final_answer": <non-empty string>}`
- [ ] Mock test: given `retrieved_docs=[doc_A, doc_B]` and `grade_results=[{score:0.8,...},{score:0.3,...}]`, only `doc_A.page_content` appears in the LLM call args

---

## T5 — `not_found` Node

### What it builds

The `not_found` node, which selects the `GradeResult` with the highest `score` and constructs the exact refusal string specified in the issue spec.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Highest score selection | `max(grade_results, key=lambda r: r["score"])` | PRD §LangGraph Nodes: "the highest score from grade_results" |
| Fallback when `grade_results` is empty | `score=0.0`, `reason="no documents retrieved"` | Defensive; routing should prevent this but an empty state must not raise |
| Score formatting | `f"{best.score:.2f}"` | Issue spec §Acceptance criteria: "score rounded to 2 decimal places" |
| Exact string template | `f"I couldn't find relevant information in the knowledge base. (Best relevance score: {best['score']:.2f} — reason: '{best['reason']}')"` | Issue spec provides the exact template; any deviation breaks acceptance criteria |

### Implementation

```python
def not_found(state: CRAGState) -> dict:
    """
    Build a structured refusal response when all reformulation attempts are exhausted.

    Returns: {"final_answer": str}
    """
    grade_results: list[GradeResult] = state.get("grade_results", [])

    if grade_results:
        best = max(grade_results, key=lambda r: r["score"])
    else:
        best = GradeResult(doc_id="", score=0.0, relevant=False, reason="no documents retrieved")

    final_answer = (
        f"I couldn't find relevant information in the knowledge base. "
        f"(Best relevance score: {best['score']:.2f} — reason: '{best['reason']}')"
    )
    return {"final_answer": final_answer}
```

### Acceptance criteria

- [ ] Output string contains the literal substring `"Best relevance score:"`
- [ ] Score is rounded to exactly 2 decimal places (e.g., `0.45` not `0.4500000000001`)
- [ ] The `reason` text appears verbatim between single quotes in the output
- [ ] Given `grade_results=[{score:0.45, reason:"off-topic"}]`, output is `"I couldn't find relevant information in the knowledge base. (Best relevance score: 0.45 — reason: 'off-topic')"`

---

## T6 — `route_after_grading` Routing Function

### What it builds

The pure routing function that LangGraph uses as the conditional edge decision from `grade_documents`. No LLM calls, no side effects.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Threshold check | `score >= GRADE_THRESHOLD` (0.7) | Consistent with `generate` and `grade_documents` — single source of truth constant |
| Iteration cap | `iteration_count < MAX_ITERATIONS` where `MAX_ITERATIONS = 2` | PRD §Relevance Grading Thresholds: cap at 2 attempts; `< 2` means iterations 0 and 1 trigger reformulation, iteration 2 triggers `not_found` |
| Return values | Exact strings `"generate"`, `"reformulate_query"`, `"not_found"` | Must match the node names registered in the graph |

### Implementation

```python
def route_after_grading(state: CRAGState) -> str:
    """
    Pure routing function for the conditional edge after grade_documents.

    Returns:
        "generate"          — at least one GradeResult has score >= 0.7
        "reformulate_query" — zero passing docs AND iteration_count < 2
        "not_found"         — zero passing docs AND iteration_count >= 2
    """
    passing = [r for r in state["grade_results"] if r["score"] >= GRADE_THRESHOLD]
    if passing:
        return "generate"
    if state["iteration_count"] < MAX_ITERATIONS:
        return "reformulate_query"
    return "not_found"
```

### Acceptance criteria

- [ ] Returns `"generate"` when at least one `GradeResult` has `score >= 0.7`
- [ ] Returns `"reformulate_query"` when all scores < 0.7 and `iteration_count == 0`
- [ ] Returns `"reformulate_query"` when all scores < 0.7 and `iteration_count == 1`
- [ ] Returns `"not_found"` when all scores < 0.7 and `iteration_count == 2`
- [ ] Returns `"not_found"` when all scores < 0.7 and `iteration_count > 2` (defensive)
- [ ] No LLM call, no I/O — function is deterministic given the same state

---

## T7 — `build_graph()` — Graph Assembly and Compilation

### What it builds

The `build_graph()` function in `graph/graph.py` that wires all nodes with `StateGraph`, adds edges, adds the conditional edge from `grade_documents`, compiles the graph, and returns the compiled object.

### Design decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Graph state class | `CRAGState` (TypedDict) | PRD §LangGraph State; TypedDict is the correct type for `StateGraph` state in LangGraph 0.2.x |
| Entry point | `retrieve` | PRD §Graph Assembly |
| Terminal nodes | `generate` and `not_found` both route to `END` | PRD §Graph Assembly |
| `reformulate_query` loop-back | `reformulate_query → retrieve` | PRD §Graph Assembly |
| Conditional edge source | `grade_documents` with path function `route_after_grading` | PRD §Graph Assembly |
| Path map in conditional edge | `{"generate": "generate", "reformulate_query": "reformulate_query", "not_found": "not_found"}` | LangGraph 0.2.x requires explicit path map in `add_conditional_edges` |
| Return type annotation | `-> Any` with comment | See Assumption #10 |

### Implementation

```python
"""LangGraph graph assembly and compilation for the CRAG pipeline."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from graph.state import CRAGState
from graph.nodes import (
    retrieve,
    grade_documents,
    reformulate_query,
    generate,
    not_found,
    route_after_grading,
)


def build_graph() -> Any:  # -> CompiledGraph (not exported as a public symbol in langgraph 0.2.x)
    """
    Assemble and compile the CRAG LangGraph state machine.

    Graph topology:
        retrieve → grade_documents
        grade_documents --[route_after_grading]--> generate | reformulate_query | not_found
        reformulate_query → retrieve  (loop)
        generate → END
        not_found → END

    Returns:
        A compiled LangGraph graph ready for .invoke() calls.
    """
    builder = StateGraph(CRAGState)

    # Register nodes
    builder.add_node("retrieve", retrieve)
    builder.add_node("grade_documents", grade_documents)
    builder.add_node("reformulate_query", reformulate_query)
    builder.add_node("generate", generate)
    builder.add_node("not_found", not_found)

    # Entry point
    builder.set_entry_point("retrieve")

    # Fixed edges
    builder.add_edge("retrieve", "grade_documents")
    builder.add_edge("reformulate_query", "retrieve")
    builder.add_edge("generate", END)
    builder.add_edge("not_found", END)

    # Conditional edge
    builder.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "generate": "generate",
            "reformulate_query": "reformulate_query",
            "not_found": "not_found",
        },
    )

    return builder.compile()
```

### Acceptance criteria

- [ ] `from graph.graph import build_graph; g = build_graph()` does not raise
- [ ] `g.invoke({"query": "...", "reformulated_query": None, "retrieved_docs": [], "grade_results": [], "final_answer": None, "iteration_count": 0})` returns a dict with `"final_answer"` key (with mocked LLMs and retriever)
- [ ] `build_graph()` is importable without `OPENAI_API_KEY` being set (no LLM or retriever constructed at import time)

---

## T8 — Unit Tests

### What it builds

`tests/test_graph.py` — pytest test suite covering all acceptance criteria from the issue spec. All LLM calls and the Chroma retriever are mocked. No `OPENAI_API_KEY` required.

### Test infrastructure

```python
"""Unit tests for graph/nodes.py and graph/graph.py.

Run with: pytest tests/test_graph.py -v
No OPENAI_API_KEY required — LLMs and retriever are mocked.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from graph.state import CRAGState, GradeResult
from graph.nodes import (
    grade_documents,
    not_found,
    generate,
    route_after_grading,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> CRAGState:
    """Return a minimal valid CRAGState with sensible defaults."""
    base: CRAGState = {
        "query": "What is CRAG?",
        "reformulated_query": None,
        "retrieved_docs": [],
        "grade_results": [],
        "final_answer": None,
        "iteration_count": 0,
    }
    base.update(overrides)
    return base


def _make_doc(content: str = "some content", source: str = "doc.pdf") -> Document:
    return Document(page_content=content, metadata={"source": source})


def _make_grade(score: float, reason: str = "test reason", doc_id: str = "doc.pdf_0") -> GradeResult:
    return GradeResult(doc_id=doc_id, score=score, relevant=score >= 0.7, reason=reason)
```

### Test cases

```python
# ---------------------------------------------------------------------------
# route_after_grading — pure function, no mocks needed
# ---------------------------------------------------------------------------

class TestRouteAfterGrading:
    def test_returns_generate_when_any_doc_passes(self):
        state = _make_state(
            grade_results=[_make_grade(0.8), _make_grade(0.3)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_generate_when_all_docs_pass(self):
        state = _make_state(
            grade_results=[_make_grade(0.9), _make_grade(0.75)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_generate_at_exact_threshold(self):
        state = _make_state(
            grade_results=[_make_grade(0.7)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_reformulate_when_no_pass_iter_0(self):
        state = _make_state(
            grade_results=[_make_grade(0.3), _make_grade(0.5)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "reformulate_query"

    def test_returns_reformulate_when_no_pass_iter_1(self):
        state = _make_state(
            grade_results=[_make_grade(0.3)],
            iteration_count=1,
        )
        assert route_after_grading(state) == "reformulate_query"

    def test_returns_not_found_when_no_pass_iter_2(self):
        state = _make_state(
            grade_results=[_make_grade(0.3)],
            iteration_count=2,
        )
        assert route_after_grading(state) == "not_found"

    def test_returns_not_found_when_no_pass_iter_above_2(self):
        state = _make_state(
            grade_results=[_make_grade(0.1)],
            iteration_count=5,
        )
        assert route_after_grading(state) == "not_found"

    def test_below_threshold_does_not_trigger_generate(self):
        state = _make_state(
            grade_results=[_make_grade(0.69)],
            iteration_count=0,
        )
        assert route_after_grading(state) != "generate"


# ---------------------------------------------------------------------------
# not_found node
# ---------------------------------------------------------------------------

class TestNotFoundNode:
    def test_exact_refusal_string_format(self):
        state = _make_state(
            grade_results=[_make_grade(0.45, reason="off-topic content")],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "Best relevance score:" in answer
        assert "0.45" in answer
        assert "off-topic content" in answer

    def test_score_rounded_to_2_decimals(self):
        state = _make_state(
            grade_results=[_make_grade(0.333333, reason="irrelevant")],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "0.33" in answer

    def test_picks_highest_score_from_multiple_results(self):
        state = _make_state(
            grade_results=[
                _make_grade(0.3, reason="low relevance"),
                _make_grade(0.55, reason="best match"),
                _make_grade(0.2, reason="completely off"),
            ],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "0.55" in answer
        assert "best match" in answer

    def test_reason_appears_verbatim(self):
        reason_text = "The document discusses unrelated financial topics"
        state = _make_state(
            grade_results=[_make_grade(0.4, reason=reason_text)],
        )
        result = not_found(state)
        assert reason_text in result["final_answer"]

    def test_returns_only_final_answer_key(self):
        state = _make_state(grade_results=[_make_grade(0.3)])
        result = not_found(state)
        assert list(result.keys()) == ["final_answer"]

    def test_empty_grade_results_does_not_raise(self):
        state = _make_state(grade_results=[])
        result = not_found(state)
        assert "final_answer" in result
        assert result["final_answer"] is not None


# ---------------------------------------------------------------------------
# grade_documents node
# ---------------------------------------------------------------------------

class TestGradeDocumentsNode:
    def _mock_grader_output(self, score: float, reason: str = "test"):
        """Return a mock GradeOutput-like object."""
        mock = MagicMock()
        mock.score = score
        mock.reason = reason
        mock.relevant = score >= 0.7
        return mock

    def test_produces_one_grade_per_doc(self):
        docs = [_make_doc("content A"), _make_doc("content B"), _make_doc("content C")]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.side_effect = [
            self._mock_grader_output(0.8),
            self._mock_grader_output(0.4),
            self._mock_grader_output(0.9),
        ]
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert len(result["grade_results"]) == 3

    def test_relevant_true_when_score_above_threshold(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(score=0.85)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert result["grade_results"][0]["relevant"] is True
        assert result["grade_results"][0]["score"] == 0.85

    def test_relevant_false_when_score_below_threshold(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(score=0.5)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert result["grade_results"][0]["relevant"] is False

    def test_relevant_computed_from_score_not_trusted_from_llm(self):
        """LLM returns relevant=True but score=0.3 — Python should set relevant=False."""
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        inconsistent_output = MagicMock()
        inconsistent_output.score = 0.3
        inconsistent_output.reason = "somewhat related"
        inconsistent_output.relevant = True  # LLM says True but score is 0.3

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = inconsistent_output
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        # Python recomputes: 0.3 < 0.7 → relevant must be False
        assert result["grade_results"][0]["relevant"] is False

    def test_returns_only_grade_results_key(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(0.6)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert list(result.keys()) == ["grade_results"]


# ---------------------------------------------------------------------------
# generate node — filtering behaviour
# ---------------------------------------------------------------------------

class TestGenerateNode:
    def test_only_passing_docs_in_context(self):
        """Only docs with score >= 0.7 must appear in the LLM call."""
        doc_a = _make_doc("relevant content", "a.pdf")
        doc_b = _make_doc("irrelevant content", "b.pdf")
        state = _make_state(
            retrieved_docs=[doc_a, doc_b],
            grade_results=[
                _make_grade(0.85, doc_id="a.pdf_0"),
                _make_grade(0.30, doc_id="b.pdf_1"),
            ],
        )

        mock_response = MagicMock()
        mock_response.content = "Generated answer."
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        captured_prompt = {}

        def capture_invoke(prompt):
            captured_prompt["value"] = prompt
            return mock_response

        mock_llm.invoke.side_effect = capture_invoke

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = generate(state)

        # doc_a content must appear in the prompt; doc_b must not
        assert "relevant content" in captured_prompt["value"]
        assert "irrelevant content" not in captured_prompt["value"]
        assert result["final_answer"] == "Generated answer."

    def test_returns_only_final_answer_key(self):
        doc = _make_doc("content")
        state = _make_state(
            retrieved_docs=[doc],
            grade_results=[_make_grade(0.9)],
        )
        mock_response = MagicMock()
        mock_response.content = "answer"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = generate(state)

        assert list(result.keys()) == ["final_answer"]


# ---------------------------------------------------------------------------
# build_graph integration smoke test
# ---------------------------------------------------------------------------

class TestBuildGraph:
    def test_build_graph_returns_compilable_graph(self):
        """build_graph() must not raise and must return an invocable object."""
        from graph.graph import build_graph

        # Mock all LLM and retriever calls to avoid API calls
        mock_docs = [_make_doc("test content")]
        mock_grade_output = MagicMock()
        mock_grade_output.score = 0.9
        mock_grade_output.reason = "highly relevant"

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = mock_grade_output

        mock_gen_response = MagicMock()
        mock_gen_response.content = "Test answer"

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        mock_llm.invoke.return_value = mock_gen_response

        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = mock_docs

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm), \
             patch("graph.nodes._get_retriever", return_value=mock_vectorstore):
            graph = build_graph()
            result = graph.invoke({
                "query": "What is CRAG?",
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
            })

        assert result is not None
        assert result.get("final_answer") is not None

    def test_iteration_count_never_exceeds_2(self):
        """Even with persistent low grades, iteration_count must stop at 2."""
        from graph.graph import build_graph

        # All docs fail grading — forces reformulation loop
        mock_docs = [_make_doc("irrelevant")]
        mock_grade_output = MagicMock()
        mock_grade_output.score = 0.1
        mock_grade_output.reason = "not relevant at all"

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = mock_grade_output

        mock_reformulate_response = MagicMock()
        mock_reformulate_response.content = "reformulated query"

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        mock_llm.invoke.return_value = mock_reformulate_response

        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = mock_docs

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm), \
             patch("graph.nodes._get_retriever", return_value=mock_vectorstore):
            graph = build_graph()
            result = graph.invoke({
                "query": "unanswerable question",
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
            })

        assert result["iteration_count"] <= 2
        assert "Best relevance score:" in result["final_answer"]
```

### Acceptance criteria

- [ ] `pytest tests/test_graph.py -v` exits with code 0
- [ ] No test requires `OPENAI_API_KEY`
- [ ] `route_after_grading` tests: all 8 branches covered (including exact threshold and above-cap iteration)
- [ ] `not_found` tests: exact string format, highest score selection, verbatim reason, empty grade_results guard
- [ ] `grade_documents` tests: one-per-doc, relevant=True/False, Python recompute overrides LLM bool
- [ ] `generate` tests: passing/failing doc filtering verified via prompt content inspection
- [ ] Integration smoke test: full graph invocation completes and returns non-None `final_answer`
- [ ] Reformulation loop cap test: `iteration_count <= 2` after full graph run with all-failing grades

---

## Migration

Not applicable. This PR introduces no database schema, no SQLAlchemy models, and no Alembic migrations. All state is ephemeral TypedDicts threaded through LangGraph — no persistence layer beyond the Chroma vector store already established in PR-2.

---

## Test quality rules

### Routing completeness via branch enumeration

```python
# All three return values must be tested independently
assert route_after_grading(state_with_passing) == "generate"
assert route_after_grading(state_no_pass_iter_0) == "reformulate_query"
assert route_after_grading(state_no_pass_iter_2) == "not_found"
```

### Threshold exactness — test at boundary value

```python
# Score == 0.7 is the exact threshold — must return "generate", not "reformulate_query"
state = _make_state(grade_results=[_make_grade(0.7)], iteration_count=0)
assert route_after_grading(state) == "generate"

# Score == 0.69 is just below — must NOT return "generate"
state = _make_state(grade_results=[_make_grade(0.69)], iteration_count=0)
assert route_after_grading(state) != "generate"
```

### `not_found` string format — exact substring assertions

```python
answer = not_found(state)["final_answer"]
assert "Best relevance score:" in answer     # required substring
assert f"{score:.2f}" in answer              # 2-decimal formatting
assert reason in answer                      # verbatim reason
```

### `generate` filtering — inspect LLM call argument

```python
# Capture the prompt passed to llm.invoke; check presence/absence of doc content
assert passing_doc_content in captured_prompt
assert failing_doc_content not in captured_prompt
```

### `grade_documents` — Python recompute overrides LLM bool

```python
# LLM says relevant=True but score=0.3 — node must set relevant=False
assert grade_results[0]["relevant"] is False  # not True
```

### Iteration cap — assert against the returned state, not a mock call count

```python
result = graph.invoke(initial_state_all_failing)
assert result["iteration_count"] <= 2
```

---

## Automated verification

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install test dependencies (dev-only, not in requirements.txt)
pip install pytest pytest-mock

# Run graph tests only
pytest tests/test_graph.py -v

# Run full test suite (includes PR2 ingest tests)
pytest tests/ -v

# Smoke-test: build_graph importable without OPENAI_API_KEY
python -c "from graph.graph import build_graph; print('build_graph import OK')"

# Smoke-test: nodes module importable without OPENAI_API_KEY
python -c "from graph.nodes import route_after_grading; print('nodes import OK')"

# Lint (if ruff is available)
ruff check graph/nodes.py graph/graph.py tests/test_graph.py
```

---

## Manual verification

1. **Smoke test — `route_after_grading` all three branches:**
   ```python
   from graph.state import GradeResult
   from graph.nodes import route_after_grading

   passing = [{"doc_id": "a_0", "score": 0.8, "relevant": True, "reason": "good match"}]
   failing = [{"doc_id": "a_0", "score": 0.3, "relevant": False, "reason": "off-topic"}]

   state_generate = {"query": "q", "reformulated_query": None, "retrieved_docs": [],
                     "grade_results": passing, "final_answer": None, "iteration_count": 0}
   state_reform   = {"query": "q", "reformulated_query": None, "retrieved_docs": [],
                     "grade_results": failing, "final_answer": None, "iteration_count": 0}
   state_notfound = {"query": "q", "reformulated_query": None, "retrieved_docs": [],
                     "grade_results": failing, "final_answer": None, "iteration_count": 2}

   assert route_after_grading(state_generate) == "generate"
   assert route_after_grading(state_reform) == "reformulate_query"
   assert route_after_grading(state_notfound) == "not_found"
   print("All routing branches OK")
   ```
   Expected output: `All routing branches OK`

2. **Smoke test — `not_found` exact string:**
   ```python
   from graph.nodes import not_found

   state = {"query": "q", "reformulated_query": None, "retrieved_docs": [],
            "grade_results": [{"doc_id": "x", "score": 0.45, "relevant": False, "reason": "off-topic"}],
            "final_answer": None, "iteration_count": 2}
   result = not_found(state)
   print(result["final_answer"])
   ```
   Expected output: `I couldn't find relevant information in the knowledge base. (Best relevance score: 0.45 — reason: 'off-topic')`

3. **`build_graph()` import test:**
   ```bash
   python -c "from graph.graph import build_graph; g = build_graph(); print(type(g))"
   ```
   Expected output: some `CompiledGraph` class name (no exception)

4. **Full pipeline invocation (requires `OPENAI_API_KEY` and ingested corpus):**
   ```python
   from graph.graph import build_graph

   graph = build_graph()
   result = graph.invoke({
       "query": "What is the main topic of the document?",
       "reformulated_query": None,
       "retrieved_docs": [],
       "grade_results": [],
       "final_answer": None,
       "iteration_count": 0,
   })
   print("Answer:", result["final_answer"])
   print("Iteration count:", result["iteration_count"])
   ```
   Expected: `final_answer` is non-None; `iteration_count` is 0, 1, or 2.

5. **Verify reformulation loop cap (requires `OPENAI_API_KEY` and low-relevance corpus):**
   - Send a query on a topic not in the corpus.
   - Observe that `iteration_count` in the result is exactly 2 and `final_answer` contains `"Best relevance score:"`.

6. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ```
   Expected: all tests pass, zero `OPENAI_API_KEY` errors.
