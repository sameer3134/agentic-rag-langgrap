# chore: project scaffold and environment

> Issue #1 | Branch `chore/project-scaffold` | Type AFK
> Depends on: None — can start immediately
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Create the full project directory structure, pin all dependencies in `requirements.txt`, provide a `.env.example` with all required environment variables, configure `.gitignore` to exclude secrets and generated data, and add empty module stubs so every import resolves before any logic is implemented. This slice produces a repo that boots cleanly and is ready for feature branches to build on.

## Resolved decisions

**Directory layout:**
```
agentic-crag-pipeline/
├── app.py                  # Streamlit entry point (stub)
├── ingest.py               # Ingestion module (stub)
├── observability.py        # Phoenix setup (stub)
├── eval.py                 # Ragas evaluation (stub)
├── graph/
│   ├── __init__.py
│   ├── state.py            # CRAGState + GradeResult TypedDicts
│   ├── nodes.py            # Node functions (stubs)
│   └── graph.py            # Graph assembly (stub)
├── data/
│   └── uploads/            # Uploaded PDFs land here
├── chroma_db/              # Chroma persist dir (gitignored)
├── phoenix_traces/         # Phoenix trace storage (gitignored)
├── .env                    # Gitignored — real secrets
├── .env.example            # Committed — template only
├── .gitignore
└── requirements.txt
```

**Required environment variables (`.env.example`):**
```
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIR=./chroma_db
PHOENIX_PORT=6006
PHOENIX_TRACE_DIR=./phoenix_traces
```

**`requirements.txt` pinned versions:**
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

**Python version:** 3.11

**`.gitignore` must exclude:** `.env`, `chroma_db/`, `phoenix_traces/`, `data/uploads/`, `data/golden_dataset.json`, `__pycache__/`, `*.pyc`, `.venv/`

**State schema (implement fully in `graph/state.py` — not a stub):**

`GradeResult` TypedDict:
```python
{ "doc_id": str, "score": float, "relevant": bool, "reason": str }
```

`CRAGState` TypedDict:
```python
{
  "query": str,
  "reformulated_query": str | None,
  "retrieved_docs": list,        # list[Document]
  "grade_results": list,         # list[GradeResult]
  "final_answer": str | None,
  "iteration_count": int
}
```

## Acceptance criteria

- [ ] Running `pip install -r requirements.txt` in a clean Python 3.11 venv completes without dependency conflicts
- [ ] `python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"` succeeds with no ImportError
- [ ] `.env` is listed in `.gitignore` and does not appear in `git status` output after creation
- [ ] `chroma_db/`, `phoenix_traces/`, `data/uploads/` are listed in `.gitignore`
- [ ] `.env.example` contains all four required environment variable keys
- [ ] `graph/state.py` defines `GradeResult` and `CRAGState` as TypedDicts with the correct fields
- [ ] `data/uploads/` directory exists and is tracked via a `.gitkeep`

## Out of scope

All business logic — ingestion, graph nodes, UI, observability, evaluation. Those are implemented in issues #2–#6.
