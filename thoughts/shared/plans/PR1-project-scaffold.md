# PR1 — chore: project scaffold and environment

**Branch:** `chore/project-scaffold`
**PR ID:** PR-1
**Depends on:** None — first PR in sequence

---

## What This PR Does

This PR creates the full project skeleton for the `agentic-crag-pipeline` repository: directory layout, pinned `requirements.txt`, `.env.example` template, `.gitignore`, and module stubs so every import resolves before any logic is written. It also implements the complete state schema (`GradeResult` and `CRAGState` TypedDicts in `graph/state.py`) since the state shape must be locked before any feature branch touches it. The result is a repo that installs cleanly in a fresh Python 3.11 venv and passes an import smoke-test with no errors.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | `data/uploads/` git tracking | `.gitkeep` file added; directory itself gitignored via `data/uploads/` rule in `.gitignore` — but `.gitkeep` is committed | Directory must exist for app startup; empty dirs are not tracked by git without a placeholder | Never — this is standard practice |
| 2 | `graph/__init__.py` content | Empty file (zero bytes) | No package-level imports needed at scaffold stage; feature branches populate it | If a convenience re-export is needed in a later PR |
| 3 | Stub file content | Each stub contains only the minimum: module docstring + `pass` (for functions) or empty class body | Keeps diffs small; any content beyond imports would conflict with feature branch work | When feature branches implement the modules |
| 4 | `python-dotenv` pin | Unpinned (latest compatible) | PRD specifies no version for `python-dotenv`; latest is stable and backward-compatible | If a breaking release occurs |
| 5 | `observability.py` stub | Top-level file (not inside `graph/`) | PRD and issue spec place it at repo root alongside `app.py`, `ingest.py`, `eval.py` | Never — matches PRD layout |
| 6 | `data/golden_dataset.json` gitignore | Included in `.gitignore` | Specified explicitly in issue spec — generated file, expensive to regenerate, not source-controlled | Never |
| 7 | `CRAGState.retrieved_docs` type annotation | `list` (not `list[Document]`) in TypedDict | TypedDict cannot hold forward-reference generics cleanly in Python 3.11 without `from __future__ import annotations`; using bare `list` keeps the schema importable without LangChain installed at type-check time. Comment documents the intended type. | If mypy strict mode is adopted — switch to `list[Document]` with the import |
| 8 | `CRAGState.grade_results` type annotation | `list` (not `list[GradeResult]`) | Same reason as assumption 7 — avoids circular import risk if `GradeResult` were ever in a separate module | Same as above |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | Directory structure + data dirs with `.gitkeep` | `data/uploads/.gitkeep`, `chroma_db/` (gitignored), `phoenix_traces/` (gitignored) |
| T2 | `.gitignore` | `.gitignore` |
| T3 | `.env.example` | `.env.example` |
| T4 | `requirements.txt` | `requirements.txt` |
| T5 | State schema (fully implemented) | `graph/__init__.py`, `graph/state.py` |
| T6 | Module stubs | `app.py`, `ingest.py`, `observability.py`, `eval.py`, `graph/nodes.py`, `graph/graph.py` |

---

## Architecture Constraints

This PR establishes the foundational layer. No business logic is implemented, so most architecture constraints apply to future PRs. Relevant constraints for this PR:

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| Python 3.11 only | PRD §Environment & Dependencies | Version-specific syntax (e.g., `str | None` union syntax) used in state schema will fail on Python < 3.10 |
| Minor-version pins in `requirements.txt` (`==0.3.*` style) | PRD §Environment & Dependencies | Silent breaking changes from patch/minor upgrades — especially `langgraph` which had breaking API changes between 0.1 and 0.2 |
| `graph/state.py` TypedDicts must be fully implemented (not stubs) | Issue spec §Resolved decisions | Every feature branch (`feat/pdf-ingestion`, `feat/crag-graph`, etc.) imports `CRAGState` — a stub would cause `AttributeError` at import |
| `.env` must be gitignored | Issue spec §Acceptance criteria | Committing `.env` exposes `OPENAI_API_KEY` to version control |
| `data/uploads/` must exist at runtime | PRD §Ingestion Module | `ingest.py` writes uploaded PDFs to this directory; `FileNotFoundError` at first upload if absent |
| `graph/` must be a Python package with `__init__.py` | Issue spec §Acceptance criteria | `from graph import state, nodes, graph` import test fails without `__init__.py` |

---

## T1 — Directory Structure

### What it builds
All required directories. `chroma_db/` and `phoenix_traces/` are gitignored so only the `.gitkeep` in `data/uploads/` is committed.

### Implementation

**`data/uploads/.gitkeep`** — empty file, zero bytes. Ensures the directory exists after `git clone`.

### Acceptance criteria
- [ ] `data/uploads/` directory exists in a fresh clone
- [ ] `chroma_db/` and `phoenix_traces/` are NOT present after a fresh clone (gitignored, no `.gitkeep`)

---

## T2 — `.gitignore`

### What it builds
Gitignore covering secrets, generated data, virtual environments, and Python bytecode.

### Implementation

```gitignore
# Secrets
.env

# Generated / persisted data
chroma_db/
phoenix_traces/
data/uploads/
data/golden_dataset.json

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
```

### Acceptance criteria
- [ ] `git status` does not show `.env` after creating that file
- [ ] `git status` does not show `chroma_db/`, `phoenix_traces/`, or `data/uploads/` contents
- [ ] `data/uploads/.gitkeep` IS tracked (`.gitkeep` not excluded)

---

## T3 — `.env.example`

### What it builds
Template file committed to version control showing all required environment variables without real values.

### Implementation

```dotenv
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIR=./chroma_db
PHOENIX_PORT=6006
PHOENIX_TRACE_DIR=./phoenix_traces
```

### Acceptance criteria
- [ ] File contains exactly the four keys: `OPENAI_API_KEY`, `CHROMA_PERSIST_DIR`, `PHOENIX_PORT`, `PHOENIX_TRACE_DIR`
- [ ] No real secrets — placeholder values only

---

## T4 — `requirements.txt`

### What it builds
Pinned dependency list for the full project. All feature branches install from this single file.

### Implementation

```
langchain==0.3.*
langgraph==0.2.*
langchain-openai==0.2.*
langchain-community==0.3.*
chromadb==0.5.*
arize-phoenix==4.*
openinference-instrumentation-langchain==0.1.*
ragas==0.1.*
streamlit==1.38.*
pypdf==4.*
python-dotenv
```

### Acceptance criteria
- [ ] `pip install -r requirements.txt` in a clean Python 3.11 venv completes without dependency conflicts
- [ ] All eleven packages are present (10 pinned + `python-dotenv` unpinned)

---

## T5 — State Schema (`graph/state.py`)

### What it builds
`GradeResult` and `CRAGState` TypedDicts. This is the ONLY module that is fully implemented in this PR (not a stub) because the state shape must be locked before feature branches start.

### Column decisions

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| `GradeResult.doc_id` | `str` | No | — | Document identifier passed from retriever |
| `GradeResult.score` | `float` | No | — | 0.0–1.0 relevance score from LLM grader |
| `GradeResult.relevant` | `bool` | No | — | Derived: `score >= 0.7` |
| `GradeResult.reason` | `str` | No | — | LLM explanation; fed to `not_found` response |
| `CRAGState.query` | `str` | No | — | Original user query, never mutated |
| `CRAGState.reformulated_query` | `str \| None` | Yes | `None` | Set by `reformulate_query` node |
| `CRAGState.retrieved_docs` | `list` | No | — | `list[Document]`; bare `list` for import safety |
| `CRAGState.grade_results` | `list` | No | — | `list[GradeResult]`; bare `list` for import safety |
| `CRAGState.final_answer` | `str \| None` | Yes | `None` | Set by `generate` or `not_found` node |
| `CRAGState.iteration_count` | `int` | No | — | Starts at 0; incremented by `reformulate_query` |

### Layer compliance checklist
- [x] TypedDicts only — no Pydantic, no dataclasses, no ORM models in `graph/state.py`
- [x] No external imports beyond `typing` and `__future__`
- [x] Importable without `OPENAI_API_KEY` set

### Implementation

**`graph/__init__.py`**
```python
# graph package
```

**`graph/state.py`**
```python
"""
LangGraph state schema for the agentic CRAG pipeline.

GradeResult and CRAGState are TypedDicts — intentionally simple dicts
with type annotations. LangGraph merges partial dicts between nodes;
mutable Pydantic models would break that merge contract.
"""
from __future__ import annotations

from typing import TypedDict


class GradeResult(TypedDict):
    """Relevance grade produced by the grade_documents node for one document."""

    doc_id: str
    score: float       # 0.0 – 1.0; threshold ≥ 0.7 passes
    relevant: bool     # score >= 0.7
    reason: str        # LLM explanation; surfaced in not_found response and Phoenix spans


class CRAGState(TypedDict):
    """
    Shared mutable state threaded through every LangGraph node.

    Immutability contract: each node returns a *partial dict* that
    LangGraph merges into the state — nodes must not mutate the input
    state dict in place.
    """

    query: str                        # Original user query — never overwritten
    reformulated_query: str | None    # Set by reformulate_query node; None on first pass
    retrieved_docs: list              # list[Document] — bare list avoids import-time LangChain dep
    grade_results: list               # list[GradeResult] — populated by grade_documents node
    final_answer: str | None          # Set by generate or not_found node
    iteration_count: int              # Starts at 0; incremented by reformulate_query
```

### Acceptance criteria
- [ ] `from graph.state import GradeResult, CRAGState` succeeds with no errors
- [ ] `GradeResult` has exactly four fields: `doc_id`, `score`, `relevant`, `reason`
- [ ] `CRAGState` has exactly six fields: `query`, `reformulated_query`, `retrieved_docs`, `grade_results`, `final_answer`, `iteration_count`
- [ ] `reformulated_query` and `final_answer` are annotated as `str | None`

---

## T6 — Module Stubs

### What it builds
Minimal stub files so the smoke-test import `python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"` passes.

### Known limitations
All stubs are intentionally empty — no business logic. Feature branches #2–#6 implement each module.

### Implementation

**`app.py`**
```python
"""Streamlit entry point — stub.

Full implementation in feat/streamlit-ui (PR #5).
"""
```

**`ingest.py`**
```python
"""PDF ingestion module — stub.

Full implementation in feat/pdf-ingestion (PR #2).

Public API (to be implemented):
    ingest(files: list[UploadedFile]) -> IngestResult
"""
```

**`observability.py`**
```python
"""Arize Phoenix observability setup — stub.

Full implementation in feat/observability (PR #4).

Public API (to be implemented):
    setup_tracing() -> None
"""
```

**`eval.py`**
```python
"""Ragas evaluation script — stub.

Full implementation in feat/ragas-eval (PR #6).

Usage (to be implemented):
    python eval.py
"""
```

**`graph/nodes.py`**
```python
"""LangGraph node functions — stubs.

Full implementation in feat/crag-graph (PR #3).

Nodes (to be implemented):
    retrieve(state: CRAGState) -> dict
    grade_documents(state: CRAGState) -> dict
    reformulate_query(state: CRAGState) -> dict
    generate(state: CRAGState) -> dict
    not_found(state: CRAGState) -> dict
    route_after_grading(state: CRAGState) -> str
"""
```

**`graph/graph.py`**
```python
"""LangGraph graph assembly and compilation — stub.

Full implementation in feat/crag-graph (PR #3).

Public API (to be implemented):
    build_graph() -> CompiledGraph
"""
```

### Layer compliance checklist
- [x] No business logic in stubs — only docstrings
- [x] No third-party imports in stubs — importable without any packages installed (except `graph/state.py` which only uses `typing`)
- [x] Docstrings document the intended public API for each module

### Acceptance criteria
- [ ] `python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"` exits with code 0
- [ ] No `SyntaxError` or `ImportError` in any stub

---

## Migration

Not applicable — this PR has no database schema changes. There are no SQLAlchemy models, Alembic migrations, or database connections in the scaffold.

---

## Test quality rules

### Smoke-test import (primary verification)
The single most important test for this PR is the import smoke-test:
```bash
python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"
```
Exit code must be 0. This validates the entire scaffold in one command.

### State schema unit tests (if a test suite is added)
When `tests/` is created in a later PR, add these for `graph/state.py`:

```python
from graph.state import GradeResult, CRAGState
import typing

def test_grade_result_fields():
    fields = GradeResult.__annotations__
    assert set(fields.keys()) == {"doc_id", "score", "relevant", "reason"}
    assert fields["doc_id"] is str
    assert fields["score"] is float
    assert fields["relevant"] is bool
    assert fields["reason"] is str

def test_crag_state_fields():
    fields = CRAGState.__annotations__
    assert set(fields.keys()) == {
        "query", "reformulated_query", "retrieved_docs",
        "grade_results", "final_answer", "iteration_count"
    }
    # Nullable fields must be Optional / Union with None
    import types
    reformulated = fields["reformulated_query"]
    final = fields["final_answer"]
    # Both should be str | None (Union[str, None])
    assert type(None) in typing.get_args(reformulated)
    assert type(None) in typing.get_args(final)
```

---

## Automated verification

```bash
# Install dependencies
pip install -r requirements.txt

# Smoke-test all imports
python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"
echo "Exit code: $?"

# Verify .env is gitignored
echo "OPENAI_API_KEY=test" > .env
git status --short | grep -v "^?? .env" && echo "FAIL: .env visible in git status" || echo "PASS: .env gitignored"
rm .env
```

---

## Manual verification

1. **Fresh install check:**
   ```bash
   python -m venv .venv-test
   source .venv-test/bin/activate   # or .venv-test\Scripts\activate on Windows
   pip install -r requirements.txt
   # Expect: no dependency conflict errors, all packages install
   ```

2. **Import smoke-test:**
   ```bash
   python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"
   # Expect: no output, exit code 0
   ```

3. **State schema correctness:**
   ```bash
   python -c "
   from graph.state import GradeResult, CRAGState
   g = GradeResult(doc_id='d1', score=0.85, relevant=True, reason='on topic')
   s = CRAGState(query='test', reformulated_query=None, retrieved_docs=[], grade_results=[], final_answer=None, iteration_count=0)
   print('GradeResult:', g)
   print('CRAGState:', s)
   "
   # Expect: both dicts printed with correct keys and values
   ```

4. **Gitignore verification:**
   ```bash
   echo "OPENAI_API_KEY=sk-real" > .env
   git status --short
   # Expect: .env does NOT appear in output
   rm .env
   ```

5. **data/uploads/.gitkeep tracked:**
   ```bash
   git ls-files data/
   # Expect: data/uploads/.gitkeep appears in output
   ```

6. **.env.example completeness:**
   ```bash
   cat .env.example
   # Expect: all four keys present: OPENAI_API_KEY, CHROMA_PERSIST_DIR, PHOENIX_PORT, PHOENIX_TRACE_DIR
   ```

---

## Implementation Notes

### T2 — .gitignore adjustment
The plan's Assumption 1 states `data/uploads/` is gitignored but `.gitkeep` is committed. The pre-existing `.gitignore` used `data/uploads/` (directory rule) which blocks all contents including `.gitkeep`. Changed rule to `data/uploads/*` with negation `!data/uploads/.gitkeep` so the directory contents are ignored but `.gitkeep` is trackable. This satisfies Assumption 1's intent exactly.

### T5 — TypedDict annotation evaluation
With `from __future__ import annotations`, `__annotations__` stores `ForwardRef` strings at runtime rather than resolved types. The plan's test code uses `typing.get_args()` directly on `__annotations__` values; to correctly evaluate `str | None`, callers must use `typing.get_type_hints(CRAGState)` instead of `CRAGState.__annotations__`. All acceptance criteria verified using `get_type_hints()` — all pass.
