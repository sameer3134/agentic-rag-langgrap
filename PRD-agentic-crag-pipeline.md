# PRD — agentic-crag-pipeline

## Problem Statement

Single-pass RAG pipelines are brittle: they retrieve documents once, pass whatever comes back to the generator, and produce hallucinated or unsupported answers when the retrieved context is irrelevant or incomplete. There is no mechanism to detect that retrieved documents are a poor match for the query, no automatic correction path, and no visibility into where in the pipeline quality degrades.

The user needs a self-correcting, agentic RAG pipeline where retrieval quality is explicitly measured before generation is attempted. When retrieved documents fail a relevance threshold, the pipeline should automatically reformulate the query and retry rather than silently producing a bad answer. When all retries are exhausted, the pipeline should return a transparent "not found" response rather than hallucinating. The entire execution path — every LLM call, retrieval call, grading decision, and reformulation — must be observable and evaluable against a synthetic golden dataset.

---

## Solution

A LangGraph state-machine-driven RAG pipeline implementing the Corrective RAG (CRAG) pattern over a closed corpus of user-uploaded PDFs. The graph routes queries through retrieval → relevance grading → conditional reformulation or generation, with a hard iteration cap that terminates in a structured "not found" response rather than a web search fallback. Arize Phoenix provides full OpenTelemetry-based observability of every node execution. Ragas evaluates pipeline quality across four metrics against a synthetic golden dataset. A Streamlit UI ties ingestion, querying, and debug visibility into a single local interface.

---

## User Stories

### Ingestion
1. As a user, I want to upload multiple PDF files via a drag-and-drop interface in the Streamlit UI, so that I can populate the knowledge base without running command-line scripts.
2. As a user, I want the system to display a per-file success or failure status after upload, so that I know exactly which PDFs were ingested and which were skipped.
3. As a user, I want re-uploading the same PDF to be a no-op, so that I don't accidentally create duplicate chunks that skew retrieval quality.
4. As a user, I want to see a clear error message when a PDF cannot be parsed (corrupted, scanned, password-protected), so that I know the file was skipped rather than silently excluded.
5. As a user, I want ingestion to continue processing remaining files when one file fails, so that a single bad PDF doesn't block the rest of the batch.
6. As a user, I want uploaded PDFs persisted to disk, so that I can verify which documents are in the knowledge base.

### Querying & CRAG Loop
7. As a user, I want to type a natural-language question and receive a grounded answer drawn from the ingested PDFs, so that I can query my document corpus without writing code.
8. As a user, I want each query to be stateless and independent, so that prior queries don't influence the context or quality of subsequent answers.
9. As a user, I want the pipeline to retrieve the top-5 most semantically similar document chunks for my query, so that the generator has the strongest available context.
10. As a user, I want each retrieved chunk to be individually scored by a relevance judge before generation, so that irrelevant chunks never reach the generator.
11. As a user, I want the pipeline to proceed to generation using only the chunks that score ≥ 0.7, so that the generator is never contaminated by low-quality context.
12. As a user, I want the pipeline to automatically reformulate my query and retry retrieval when all retrieved chunks score below 0.7, so that a poorly-phrased query gets a second chance before failing.
13. As a user, I want the reformulation loop to be capped at 2 attempts, so that the pipeline doesn't run indefinitely or accrue unbounded LLM cost on an unanswerable query.
14. As a user, I want a "not found" response when all reformulation attempts are exhausted, so that I receive an honest answer rather than a hallucinated one.
15. As a user, I want the "not found" response to include the best relevance score achieved and the judge's reason, so that I understand why the query failed and can rephrase it manually.

### Streamlit UI
16. As a user, I want the final generated answer displayed prominently at the top of the response area, so that I can read the answer without scrolling through debug information.
17. As a user, I want a collapsible "Debug / Trace" panel beneath the answer showing the retrieved chunks with their individual grade scores, so that I can inspect what evidence supported the answer.
18. As a user, I want the debug panel to show the reformulation history (original query → each reformulated query), so that I can understand how the pipeline transformed my input.
19. As a user, I want the debug panel to show the total iteration count for the query, so that I can see whether reformulation was triggered.
20. As a user, I want the UI to show a spinner or loading indicator while the pipeline is running, so that I know the system is working and not frozen.
21. As a user, I want the Arize Phoenix trace UI to launch automatically when the app starts, so that I can monitor live traces on port 6006 without a separate setup step.

### Observability
22. As a developer, I want every LLM call (grader and generator) to be captured as an OpenTelemetry span in Arize Phoenix, so that I can profile token usage and latency per call.
23. As a developer, I want every retriever call to be captured as a span, so that I can measure retrieval latency independently of LLM latency.
24. As a developer, I want every LangGraph node execution to appear as a named span in Phoenix, so that I can reconstruct the full execution path of any query.
25. As a developer, I want the grade score and reason from each grading call to appear in the span attributes, so that I can filter Phoenix traces by relevance quality.
26. As a developer, I want traces persisted to disk, so that I can review historical traces across sessions.

### Evaluation
27. As a developer, I want a `eval.py` script I can run on demand to measure pipeline quality, so that I can iterate on chunking parameters without deploying anything.
28. As a developer, I want a synthetic golden dataset of ~50 Q&A pairs generated from the ingested PDFs using Ragas `TestsetGenerator`, so that evaluation questions are grounded in the actual corpus.
29. As a developer, I want `eval.py` to measure Faithfulness, Context Recall, Answer Relevancy, and Context Precision, so that I have coverage across both retrieval and generation quality dimensions.
30. As a developer, I want `eval.py` to print a pass/fail table showing each metric against its threshold (Faithfulness ≥ 0.85, Context Recall ≥ 0.80, Answer Relevancy ≥ 0.80, Context Precision ≥ 0.75), so that I can immediately see which dimensions need improvement.

---

## Implementation Decisions

### Ingestion Module
- **PDF parsing:** `pypdf` (single loader, no OCR dependency). Attempt text extraction; if extracted text is empty or throws, classify as a parse failure.
- **Deduplication:** Compute SHA256 hash of the raw PDF bytes before chunking. Store the hash as a Chroma metadata field `doc_hash`. On upload, query Chroma for any existing chunk with that hash; if found, skip ingestion and report the file as "already ingested."
- **Chunking:** `RecursiveCharacterTextSplitter` with chunk_size=1000 tokens (approximated as characters × 0.75), chunk_overlap=200 tokens. This splitter respects paragraph and sentence boundaries by splitting on `["\n\n", "\n", " ", ""]` in order.
- **Embedding:** OpenAI `text-embedding-3-small` (1536 dimensions). Called via `langchain-openai` `OpenAIEmbeddings`.
- **Vector store:** Chroma with `persist_directory` set from `CHROMA_PERSIST_DIR` env var. Collection name: `"crag_corpus"`.
- **Return contract:** `IngestResult` with three lists — `ingested: list[str]` (filenames successfully ingested), `skipped: list[str]` (dedup hits), `failed: list[str]` (parse errors with reason).

### LangGraph State
- **`GradeResult`:** TypedDict with `doc_id: str`, `score: float`, `relevant: bool`, `reason: str`.
- **`CRAGState`:** TypedDict with `query: str`, `reformulated_query: str | None`, `retrieved_docs: list[Document]`, `grade_results: list[GradeResult]`, `final_answer: str | None`, `iteration_count: int`.
- State is immutable between nodes — each node returns a partial dict that LangGraph merges.

### LangGraph Nodes
- **`retrieve`:** Embeds the active query (`reformulated_query` if set, else `query`), runs Chroma similarity search top-5, updates `retrieved_docs`.
- **`grade_documents`:** Calls `gpt-4o-mini` for each retrieved doc individually via a structured output chain with Pydantic schema `{ relevant: bool, score: float, reason: str }`. Updates `grade_results`.
- **`reformulate_query`:** Calls `gpt-4o-mini` with a prompt containing the original query and the highest-scoring failed `reason` field. Returns a reformulated query string. Increments `iteration_count`.
- **`generate`:** Filters `retrieved_docs` to only those with `grade_results[i].score ≥ 0.7`. Passes filtered docs as context to `gpt-4o` for answer generation. Updates `final_answer`.
- **`not_found`:** Selects the highest `score` from `grade_results`. Builds the structured refusal string: `"I couldn't find relevant information in the knowledge base. (Best relevance score: {score:.2f} — reason: '{reason}')"`. Updates `final_answer`.

### Graph Assembly & Routing
- Single conditional edge exits `grade_documents` via a `route_after_grading(state: CRAGState) -> str` function:
  - Any `grade_result.score ≥ 0.7` exists → return `"generate"`
  - No passing docs AND `iteration_count < 2` → return `"reformulate_query"`
  - No passing docs AND `iteration_count ≥ 2` → return `"not_found"`
- Graph entry point: `retrieve`. Terminal nodes: `generate` and `not_found` both route to `END`.

### Relevance Grading Thresholds
- Pass threshold: score ≥ 0.7 → chunk included in generation context.
- Reformulation trigger: zero passing chunks AND iteration < 2.
- Terminal failure: zero passing chunks AND iteration ≥ 2 → `not_found`.

### LLM Assignment
- Grader (`grade_documents`, `reformulate_query`): `gpt-4o-mini` — low-complexity tasks, cost-sensitive.
- Generator (`generate`): `gpt-4o` — highest output quality, hallucination resistance.

### Observability
- Phoenix launched in-process via `px.launch_app(notebook_environment="streamlit")` at Streamlit startup on `PHOENIX_PORT` (default 6006). Traces persisted to `PHOENIX_TRACE_DIR`.
- Auto-instrumented via `openinference-instrumentation-langchain` `LangChainInstrumentor().instrument()` — captures all LLM calls, retriever calls, and LangGraph node spans without manual span wrapping.
- `GradeResult.score` and `GradeResult.reason` attached as span attributes so Phoenix traces are filterable by quality tier.

### Evaluation
- `TestsetGenerator` from Ragas generates ~50 Q&A pairs from the ingested `Document` objects. Dataset saved to `data/golden_dataset.json` so it isn't regenerated on every eval run.
- Pipeline invoked for each question in the dataset; retrieved context and generated answer captured.
- Ragas `evaluate()` called with metrics: `faithfulness`, `context_recall`, `answer_relevancy`, `context_precision`.
- Pass/fail table printed to stdout with columns: metric name, score, threshold, pass/fail.

### Environment & Dependencies
- Python 3.11. Key pins: `langchain==0.3.x`, `langgraph==0.2.x`, `langchain-openai==0.2.x`, `langchain-community==0.3.x`, `chromadb==0.5.x`, `arize-phoenix==4.x`, `openinference-instrumentation-langchain==0.1.x`, `ragas==0.1.x`, `streamlit==1.38.x`, `pypdf==4.x`.
- Required env vars: `OPENAI_API_KEY`, `CHROMA_PERSIST_DIR` (default `./chroma_db`), `PHOENIX_PORT` (default `6006`), `PHOENIX_TRACE_DIR` (default `./phoenix_traces`).

---

## Testing Decisions

### What makes a good test
Test only the externally observable behavior of each module — inputs and outputs. Do not test implementation details like which internal functions were called, prompt templates, or Chroma collection internals. A good test breaks when behavior changes, not when implementation changes.

### Modules to test

**`ingest.py`**
- Dedup: given a Chroma store that already contains a chunk with hash H, ingesting a PDF with the same hash must return the file in `skipped` and add zero new chunks to Chroma.
- Chunking: given a known PDF with known text length, verify the ingested chunk count falls within the expected range for 1000-token chunks with 200-token overlap.
- Error handling: given a file with no extractable text (empty bytes, or a file that pypdf raises on), verify the file appears in `failed` with a non-empty reason, and the remaining files in the batch are still ingested.
- Dedup metadata: verify the `doc_hash` metadata field on ingested chunks matches the SHA256 of the source file bytes.

**`graph/nodes.py`**
- `grade_documents` routing: given a mocked LLM that returns a pre-set score, verify that `grade_results` contains one entry per retrieved doc, each with the correct `relevant` bool based on the 0.7 threshold.
- `route_after_grading` (pure function, no LLM): verify all three branches — at least one pass returns `"generate"`, zero pass + iteration 0 returns `"reformulate_query"`, zero pass + iteration 2 returns `"not_found"`.
- `not_found` output: given a `CRAGState` with known `grade_results`, verify the output `final_answer` string contains the highest score and its reason verbatim.
- `generate` filtering: given `grade_results` with a mix of passing and failing docs, verify only passing docs appear in the context passed to the LLM (mock the LLM call).

**`eval.py`**
- Pass/fail table: given a mock `EvalResults` dict with known scores, verify the printed table marks metrics above threshold as PASS and below as FAIL.
- Threshold values: verify the hardcoded thresholds match the spec (Faithfulness 0.85, Context Recall 0.80, Answer Relevancy 0.80, Context Precision 0.75) — guards against accidental edits.

---

## Dependencies & Sequencing

The natural build order follows the data flow — each layer depends on the one below it being stable.

1. **Environment & schema** — `.env` config loading and `graph/state.py` TypedDicts. Everything else depends on the state shape being locked.
2. **Ingestion module** — depends only on environment config and external libraries (pypdf, Chroma, OpenAI). No graph dependency. Can be built and tested in isolation first; the vector store it populates is the foundation for retrieval.
3. **LangGraph nodes** — depend on the state schema (step 1) and a populated Chroma store (step 2). Each node can be implemented and unit-tested independently since they are pure state-in / state-out functions.
4. **Graph assembly & routing** — depends on all nodes existing. The routing function `route_after_grading` is a pure function that can be tested before the full graph is wired.
5. **Observability setup** — depends on the graph existing (instruments it). Can be added as a thin wrapper after the graph runs end-to-end.
6. **Streamlit UI** — depends on ingestion (step 2) and the compiled graph (step 4). Built last since it is purely a presentation layer over already-tested logic.
7. **Evaluation** — depends on ingestion (step 2) and the compiled graph (step 4). Can be developed in parallel with the UI once the graph is functional. Golden dataset generation (Ragas `TestsetGenerator`) requires an ingested corpus, so ingestion must be complete first.

---

## Out of Scope

- **Web search fallback** — the corpus is intentionally closed. Answers are grounded strictly in ingested PDFs. Web search introduces unvetted sources and hallucination risk.
- **OCR for scanned PDFs** — adds a heavy Tesseract dependency for an edge case on a 50-doc corpus. Scanned PDFs are surfaced as parse errors.
- **Multi-turn conversation / chat history** — each query is stateless. Conversational context management is a future concern.
- **Authentication or access control** — local-only deployment for a portfolio project. No multi-user or production hosting.
- **Cloud deployment** — Streamlit Community Cloud, Docker, or any hosted environment. `streamlit run app.py` on localhost is the only supported run mode.
- **CI/CD integration for evaluation** — `eval.py` is a manual on-demand script. Automated evaluation gates are a future concern.
- **Hybrid search (BM25 + semantic)** — pure vector similarity retrieval. Keyword search fusion is a future optimization.
- **Multi-format corpus** — PDF only. HTML, markdown, Word, and other formats are out of scope.

---

## Further Notes

- **Chunking iteration workflow:** the primary use of `eval.py` is to drive chunking parameter decisions. The recommended starting point (chunk_size=1000, overlap=200) is a baseline — if Context Recall scores below 0.80, increase overlap; if Context Precision scores below 0.75, reduce chunk size. Re-run `eval.py` after each change.
- **Golden dataset lifecycle:** generate the golden dataset once after the initial corpus is ingested and save it to `data/golden_dataset.json`. Regenerating it on every eval run is expensive (LLM calls) and changes the evaluation target, making metric trends uninterpretable.
- **Phoenix trace volume:** with 50-doc corpus and local usage, trace volume is low enough that disk persistence is fine indefinitely. No retention policy needed.
- **LangGraph version sensitivity:** LangGraph 0.1 → 0.2 changed the graph compilation API significantly. Pin to `langgraph==0.2.x` and do not upgrade without reviewing the conditional edge and `TypedDict` state APIs.
- **`gpt-4o-mini` structured output:** use LangChain's `.with_structured_output()` with a Pydantic model for the grader — it handles JSON mode and retry-on-parse-failure automatically, which is critical for a node that runs 5 times per query.
