# Grilling log — agentic-crag-pipeline

## Problem statement
Design and build a production-grade, self-correcting agentic RAG pipeline using:
- **LangGraph** — state-machine-driven routing to eliminate hallucinations and brittle single-pass retrieval
- **CRAG (Corrective RAG)** — structured LLM judges grade document relevance; low-confidence results trigger automated query reformulation; exhausted retries return a "not found" response (no web search — corpus is closed)
- **Arize Phoenix** — full-stack observability via OpenTelemetry; profiling multi-turn agent execution paths, nested tool calls, token bottlenecks
- **Ragas** — pipeline evaluation against a synthetic golden dataset, optimizing chunking strategies for Faithfulness and Context Recall

## Q&A

### Q1 — What is the document corpus? Format, volume, and size?
- **Answer:** PDF only, up to 50 documents, max 10 MB per document
- **Rationale:** Bounded corpus keeps indexing cost low and makes chunking iteration fast; PDF-only keeps the parsing path simple (single loader)
- **Source:** user

### Q2 — What chunking strategy and parameters?
- **Answer:** Recursive character splitter, ~1000-token chunks, 200-token overlap
- **Rationale:** Respects paragraph/sentence boundaries, overlap prevents context loss at split points, aligns with Ragas benchmark baselines for Faithfulness scoring
- **Source:** recommendation accepted

### Q3 — What embedding model and vector store?
- **Answer:** OpenAI `text-embedding-3-small` + Chroma (local, persistent on disk)
- **Rationale:** `3-small` best cost/quality ratio at 1536 dims; Chroma needs no external infrastructure for a 50-doc corpus
- **Source:** recommendation accepted

### Q4 — What LLM for the relevance judge vs. answer generator?
- **Answer:** `gpt-4o-mini` for relevance grading, `gpt-4o` for final answer generation
- **Rationale:** Grading is a simple binary/scored task — mini is fast and cheap; generation demands higher reasoning quality to avoid hallucination
- **Source:** recommendation accepted

### Q5 — What is the relevance grading schema and threshold logic?
- **Answer:** Structured output `{ relevant: bool, score: float (0.0–1.0), reason: string }`. Thresholds: ≥ 0.7 → proceed to generation; 0.4–0.69 → query reformulation + re-retrieve; < 0.4 AND iteration ≥ 2 → `not_found` response
- **Rationale:** Two-tier retry avoids burning reformulation attempts on completely off-topic queries; reason field feeds Arize Phoenix traces for debugging. No web search — corpus is closed (see Q7)
- **Source:** recommendation accepted

### Q6 — What is the LangGraph state object shape and loop cap?
- **Answer:** State: `{ query: str, reformulated_query: str|None, retrieved_docs: list[Document], grade_results: list[GradeResult], final_answer: str|None, iteration_count: int }`. Max 2 reformulation attempts before forcing `not_found` response (no web search — see Q7).
- **Rationale:** Explicit iteration cap prevents infinite loops and bounds per-query LLM cost; all fields needed for downstream Arize Phoenix tracing
- **Source:** recommendation accepted

### Q7 — Web search fallback or "not found"?
- **Answer:** No web search fallback. If vector DB retrieval scores below threshold after max reformulation attempts, the pipeline returns a "not found" / "I don't have enough information" response rather than going to the web.
- **Rationale:** Keeps the corpus closed — answers are grounded strictly in the ingested PDFs; avoids hallucination risk from unvetted web sources
- **Source:** user

### Q8 — What does the "not found" response look like?
- **Answer:** Structured refusal: hardcoded template + best grade score + reason. E.g. `"I couldn't find relevant information in the knowledge base. (Best relevance score: 0.31 — reason: 'documents discuss X, query asks about Y')"`
- **Rationale:** Transparent enough to debug via Arize Phoenix traces; clean enough to surface to end users
- **Source:** recommendation accepted

### Q9 — Retriever top-k, grading granularity, and partial-pass logic?
- **Answer:** top-5 retrieval. Each doc graded individually. Proceed to generation using only passing docs (score ≥ 0.7). Trigger reformulation only if zero docs pass.
- **Rationale:** Partial-pass logic maximizes signal per retrieval call; zero-pass threshold avoids reformulation on queries that already have some good context
- **Source:** user (top-5), recommendation accepted (grading logic)

### Q10 — LangGraph node graph: named nodes, edges, and conditional routing?
- **Answer:** Nodes: `retrieve`, `grade_documents`, `reformulate_query`, `generate`, `not_found`. Conditional edge out of `grade_documents`: any doc passes → `generate → END`; zero pass + iteration < 2 → `reformulate_query → retrieve` (loop); zero pass + iteration ≥ 2 → `not_found → END`.
- **Rationale:** Minimal node count, single conditional branch point keeps the graph readable and traceable in Phoenix
- **Source:** recommendation accepted

### Q11 — How is the pipeline exposed to users?
- **Answer:** Streamlit UI
- **Rationale:** Chat interface with minimal boilerplate; can display retrieved docs, grade scores, and final answer in one view; fast to iterate
- **Source:** user

### Q12 — What does the Streamlit UI surface beyond the final answer?
- **Answer:** Final answer prominent at top; collapsible "Debug / Trace" panel below with: retrieved docs + individual grade scores, reformulation history (original → reformulated queries), and iteration count
- **Rationale:** Clean default view for users; full visibility for debugging and demoing the CRAG loop without cluttering the main interface
- **Source:** recommendation accepted

### Q13 — How are PDFs ingested, and how is deduplication handled?
- **Answer:** Upload button in Streamlit UI (drag-and-drop, multi-file). Deduplication via SHA256 hash stored in Chroma metadata — re-upload of same file skips re-ingestion entirely.
- **Rationale:** In-UI upload keeps the workflow self-contained; hash-based dedup prevents duplicate chunks that would inflate retrieval scores
- **Source:** recommendation accepted

### Q14 — How is Arize Phoenix deployed and what is instrumented?
- **Answer:** Local in-process (`px.launch_app()`), UI on port 6006, traces persisted to disk. Auto-instrumented via `openinference-instrumentation-langchain` — captures LLM calls, retriever calls, grader calls, and LangGraph node spans automatically.
- **Rationale:** Zero infrastructure for a local project; auto-instrumentor covers the full execution tree in one line without manual span wrapping
- **Source:** recommendation accepted

### Q15 — How is Ragas evaluation run and what is the golden dataset?
- **Answer:** Manual `eval.py` script run on-demand. ~50 LLM-generated Q&A pairs produced once from the ingested PDFs using Ragas `TestsetGenerator`. Metrics: Faithfulness and Context Recall.
- **Rationale:** Sufficient statistical signal for a 50-doc corpus; no CI overhead needed for a local project; Ragas TestsetGenerator ensures questions are grounded in the actual corpus
- **Source:** recommendation accepted

### Q16 — Project directory structure?
- **Answer:**
  ```
  agentic-crag-pipeline/
  ├── app.py                  # Streamlit entry point
  ├── ingest.py               # PDF loading, chunking, embedding
  ├── graph/
  │   ├── state.py            # LangGraph state TypedDict
  │   ├── nodes.py            # retrieve, grade, reformulate, generate, not_found
  │   └── graph.py            # graph assembly + compile
  ├── eval.py                 # Ragas evaluation script
  ├── data/uploads/           # uploaded PDFs stored here
  ├── chroma_db/              # persisted Chroma vector store
  ├── phoenix_traces/         # Arize Phoenix trace storage
  ├── .env                    # OPENAI_API_KEY etc.
  └── requirements.txt
  ```
- **Rationale:** Flat enough to navigate quickly; graph/ module isolates LangGraph concerns; data dirs separated from code for clean .gitignore
- **Source:** recommendation accepted

### Q17 — Required environment variables?
- **Answer:** `OPENAI_API_KEY`, `CHROMA_PERSIST_DIR=./chroma_db`, `PHOENIX_PORT=6006`, `PHOENIX_TRACE_DIR=./phoenix_traces`
- **Rationale:** Minimal set; Ragas reuses OPENAI_API_KEY for TestsetGenerator; paths configurable without code changes
- **Source:** recommendation accepted

### Q18 — Python version and key package versions?
- **Answer:** Python 3.11, `langchain==0.3.x`, `langgraph==0.2.x`, `langchain-openai==0.2.x`, `langchain-community==0.3.x`, `chromadb==0.5.x`, `arize-phoenix==4.x`, `openinference-instrumentation-langchain==0.1.x`, `ragas==0.1.x`, `streamlit==1.38.x`, `pypdf==4.x`
- **Rationale:** Minor-version pins prevent silent breaking changes; LangGraph 0.1→0.2 had significant API surface changes
- **Source:** recommendation accepted

### Q19 — Error handling for unparseable PDFs?
- **Answer:** Per-file error surfaced in Streamlit UI, file skipped, ingestion continues for remaining files. No OCR fallback. Error logged to console.
- **Rationale:** Avoids silent data gaps; no Tesseract dependency for an edge case on a 50-doc corpus
- **Source:** recommendation accepted

### Q20 — Authentication and deployment target?
- **Answer:** Local only, no auth. `streamlit run app.py` on localhost. Deployment out of scope.
- **Rationale:** Portfolio/demo project — no multi-user or production hosting requirements
- **Source:** recommendation accepted

### Q21 — Ragas metrics and passing thresholds?
- **Answer:** Four metrics: Faithfulness ≥ 0.85, Context Recall ≥ 0.80, Answer Relevancy ≥ 0.80, Context Precision ≥ 0.75. `eval.py` prints a pass/fail table.
- **Rationale:** Four metrics cover the full retrieval-generation quality surface; thresholds are industry-standard baselines for production RAG; pass/fail table makes chunking iteration decisions obvious
- **Source:** recommendation accepted

### Q22 — Multi-turn conversation or stateless queries?
- **Answer:** Stateless — each query is fully independent, no chat history
- **Rationale:** Keeps LangGraph state minimal; avoids context window bloat; correct scope for a portfolio project; multi-turn can be added later
- **Source:** recommendation accepted

## Open / deferred
