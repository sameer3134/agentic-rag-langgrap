# High-Level Design — Agentic CRAG Pipeline

## 1. Overview

This project is a **production-grade Retrieval-Augmented Generation (RAG) system** built around the **Corrective RAG (CRAG)** pattern. Instead of blindly using retrieved documents to generate an answer, the pipeline grades each retrieved chunk for relevance, self-corrects by reformulating the query when retrieval fails, and only generates an answer when it has sufficient evidence.

The system supports **multiple users from different devices** with complete document isolation — each user's PDFs are stored in a private vector collection and never mixed with another user's data.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Browser / Streamlit Cloud                     │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │                   Streamlit UI  (app.py)                     │   │
│   │                                                              │   │
│   │  ┌─────────────┐    ┌───────────────┐   ┌───────────────┐   │   │
│   │  │ Name Modal  │    │  PDF Upload   │   │  Query Box    │   │   │
│   │  │ (@st.dialog)│    │  + Ingest Btn │   │ (chat_input)  │   │   │
│   │  └──────┬──────┘    └──────┬────────┘   └──────┬────────┘   │   │
│   │         │                  │                    │            │   │
│   │  session_state.            │                    │            │   │
│   │  collection_name           ▼                    ▼            │   │
│   └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
          │                       │                    │
          │ (slug name)           │ (file paths        │ (query string)
          │                       │  + collection)     │
          ▼                       ▼                    ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│  build_graph()   │   │  ingest_pdfs()   │   │   graph.invoke()     │
│  graph/graph.py  │   │   ingest.py      │   │  (CRAG state machine)│
│                  │   │                  │   │                      │
│  Compiles once   │   │  SHA256 dedup    │   │  retrieve            │
│  per collection  │   │  pypdf parse     │   │  → grade_documents   │
│  (@cache_resource│   │  chunk + embed   │   │  → route             │
│  keyed by name)  │   │  → Chroma write  │   │  → generate /        │
└──────────────────┘   └──────────────────┘   │    reformulate /     │
          │                       │            │    not_found         │
          └──────────┬────────────┘            └──────────────────────┘
                     │                                    │
                     ▼                                    │
          ┌────────────────────────┐                     │
          │   ChromaDB             │◄────────────────────┘
          │   (local / persistent) │  (similarity_search per query)
          │                        │
          │  crag_alice/           │  ← User A's private collection
          │  crag_bob/             │  ← User B's private collection
          │  crag_john_doe/        │  ← User C's private collection
          └────────────────────────┘
                     │
          ┌──────────┴──────────────────────────────────┐
          │            OpenAI API                        │
          │  text-embedding-3-small  (ingest + retrieve) │
          │  gpt-4o-mini             (grade + reformulate│
          │  gpt-4o                  (generate answer)   │
          └──────────────────────────────────────────────┘
                     │
          ┌──────────┴───────────────┐
          │   Arize Phoenix           │
          │   (localhost:6006)        │
          │   OTLP traces via         │
          │   LangChain instrumentor  │
          └───────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Streamlit UI (`app.py`)

| Responsibility | Detail |
|---|---|
| **Name modal** | `@st.dialog` shown on every new session. User enters their name → `collection_name = crag_{slugified_name}` stored in `st.session_state`. Nothing else renders until this is set. |
| **Resource caching** | `@st.cache_resource` keyed on `collection_name` — one compiled graph per user, built once per server process. |
| **PDF upload** | `st.file_uploader` → saves to `data/uploads/` → calls `ingest_pdfs(paths, collection_name)` on "Ingest" button click. |
| **Query** | `st.chat_input` → `graph.invoke(initial_state)` → renders `final_answer` + collapsible debug panel. |
| **Debug panel** | Shows each retrieved document with PASS/FAIL score badge, reformulation history, iteration count. |
| **Secrets** | `_load_secrets()` loads from `.env` (local) or `st.secrets` (Streamlit Cloud). |

---

### 3.2 PDF Ingestion (`ingest.py`)

```
file_path  ──►  SHA256 hash  ──►  already in Chroma?  ──►  SKIP (skipped[])
                                         │ no
                                         ▼
                               pypdf.PdfReader
                                         │
                               page-by-page text extraction
                                         │
                               RecursiveCharacterTextSplitter
                               chunk_size=1000, overlap=200
                                         │
                               langchain_chroma.Chroma.add_documents()
                               metadata: { source, doc_hash, page }
                                         │
                                    ingested[]
```

**Key design decisions:**
- Dedup is **content-based (SHA256)**, not filename-based. Re-uploading the same file under a different name is still a skip.
- Each file is processed independently — a corrupt file in a batch does not abort the rest.
- `IngestResult` returns three lists: `ingested`, `skipped`, `failed` (with reason string).
- The collection name is a parameter, never hardcoded — this is the isolation boundary.

---

### 3.3 CRAG Graph (`graph/graph.py`, `graph/nodes.py`)

The core of the system is a **LangGraph state machine** implementing Corrective RAG.

#### State Schema (`CRAGState`)

```python
CRAGState = {
    query:               str,           # original user question
    reformulated_query:  Optional[str], # rewritten query after failed grading
    retrieved_docs:      list,          # top-5 Chroma results
    grade_results:       list,          # GradeResult per doc
    final_answer:        Optional[str], # populated by generate or not_found
    iteration_count:     int,           # reformulation attempts so far
    user_id:             str,           # display name (for tracing)
}
```

#### Graph Topology

```
START
  │
  ▼
retrieve          ← searches user's private Chroma collection (top-5)
  │
  ▼
grade_documents   ← calls gpt-4o-mini once per doc, scores 0.0–1.0
  │
  ▼
route_after_grading  (pure function — no LLM)
  │
  ├─── any score ≥ 0.7 ──────────────────► generate ──────────► END
  │                                          (gpt-4o, passing
  │                                           docs as context)
  │
  ├─── no pass AND iteration_count < 2 ──► reformulate_query
  │                                          (gpt-4o-mini rewrites
  │                                           query) ──► retrieve  (loop)
  │
  └─── no pass AND iteration_count ≥ 2 ──► not_found ──────────► END
                                             (structured refusal
                                              with best score)
```

#### Node Details

| Node | LLM | Purpose |
|---|---|---|
| `retrieve` | — | Embeds query with `text-embedding-3-small`, similarity search top-5 from user's collection |
| `grade_documents` | `gpt-4o-mini` | One structured-output call per doc, returns `score: float` + `reason: str` |
| `route_after_grading` | — | Pure Python routing — `score ≥ 0.7` = pass |
| `reformulate_query` | `gpt-4o-mini` | Rewrites the query using the best-failure reason as a hint |
| `generate` | `gpt-4o` | Answers the question using only passing docs as context, cites sources |
| `not_found` | — | Returns structured refusal: `"couldn't find... (best score: X.XX — reason: '...')"` |

#### Lazy Initialisation

All resources (Chroma client, ChatOpenAI instances) are created **lazily on first node call** using `nonlocal` singletons inside `make_nodes()`. Graph compilation is pure Python — no network or disk calls at build time. This prevents version-mismatch TypeErrors on Streamlit Cloud.

---

### 3.4 Per-User Isolation Design

```
User enters "Alice"
      │
      ▼
collection_name = "crag_alice"     ← slugify("Alice")
      │
      ├── ingest_pdfs(paths, "crag_alice")  → Chroma collection: crag_alice
      │
      └── build_graph("crag_alice")
              │
              └── make_nodes("crag_alice")
                      │
                      └── Chroma(collection_name="crag_alice", ...)
                              │
                              └── retrieve() only searches crag_alice
```

User "Bob" gets `crag_bob` — a completely separate Chroma collection. Alice's documents are never visible to Bob's queries, and vice versa.

The graph is cached with `@st.cache_resource` keyed on `collection_name`, so each user gets one compiled graph instance that persists for the server's lifetime.

---

### 3.5 Observability (`observability.py`)

- Connects to an **Arize Phoenix** server via **OTLP** (`http://localhost:{PHOENIX_PORT}/v1/traces`)
- Registers the `LangChainInstrumentor` which auto-instruments every LLM call and LangGraph node as named spans
- Idempotent (`_initialized` guard) — safe to call on every Streamlit rerun
- Best-effort: all failures are caught and logged as warnings so the app never breaks if Phoenix is unavailable

Traces captured per query:
- `RETRIEVER` span: query text, k, collection name
- `LLM` span per `grade_documents` call: prompt, score, reason
- `LLM` span for `reformulate_query` / `generate`
- `CHAIN` span per LangGraph node

---

### 3.6 Evaluation (`eval.py`)

Offline quality measurement using **Ragas**:

```
Chroma corpus
      │
      ▼
TestsetGenerator (gpt-4o)
      │ generates ~50 Q&A pairs
      ▼
data/golden_dataset.json   ← cached, not regenerated on subsequent runs
      │
      ▼
graph.invoke() × 50 questions
      │
      ▼
Ragas evaluate()
      │
      ▼
Pass/Fail table
```

| Metric | Threshold |
|---|---|
| Faithfulness | ≥ 0.85 |
| Context Recall | ≥ 0.80 |
| Answer Relevancy | ≥ 0.80 |
| Context Precision | ≥ 0.75 |

---

## 4. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **UI** | Streamlit | `≥ 1.38` |
| **Orchestration** | LangGraph | `0.2.*` |
| **LLM framework** | LangChain | `0.3.*` |
| **LLM provider** | OpenAI (`gpt-4o`, `gpt-4o-mini`, `text-embedding-3-small`) | via `langchain-openai 0.2.*` |
| **Vector store** | ChromaDB (embedded, local-persist) | `≥ 0.4, < 0.6` |
| **LangChain-Chroma bridge** | langchain-chroma | `≥ 0.1.2` |
| **PDF parsing** | pypdf | `≥ 4.0` |
| **Text splitting** | langchain-text-splitters | via `langchain 0.3.*` |
| **Observability** | Arize Phoenix + OpenInference | optional |
| **Evaluation** | Ragas | optional |
| **Config** | python-dotenv | — |

---

## 5. Data Flow — End to End

### 5.1 Document Ingestion

```
1. User opens app
2. Name modal → "Alice" → collection_name = "crag_alice"
3. User uploads report.pdf
4. Clicks "Ingest"
5. report.pdf saved to data/uploads/report.pdf
6. ingest_pdfs([Path("data/uploads/report.pdf")], "crag_alice")
7. SHA256(report.pdf bytes) computed
8. Chroma checked: hash not found → proceed
9. pypdf extracts text page by page
10. RecursiveCharacterTextSplitter splits into ~1000-char chunks with 200 overlap
11. Each chunk embedded: OpenAI text-embedding-3-small → 1536-dim vector
12. Vectors + metadata (source, doc_hash, page) stored in crag_alice collection
13. UI: "Ingested: report.pdf"
```

### 5.2 Query Processing

```
1. User types: "What are the key findings?"
2. graph.invoke({ query: "...", ..., user_id: "Alice" })

[Node: retrieve]
3. "What are the key findings?" → text-embedding-3-small → 1536-dim vector
4. Chroma crag_alice similarity_search(k=5) → 5 Document chunks

[Node: grade_documents]
5. For each of 5 docs:
   gpt-4o-mini(structured) → { score: 0.85, reason: "directly answers..." }
6. grade_results = [GradeResult × 5]

[route_after_grading]
7. Any score ≥ 0.7? → Yes (score=0.85) → route to generate

[Node: generate]
8. Filter docs with score ≥ 0.7 → 3 passing docs
9. Build context string with [source · page] headers
10. gpt-4o → "The key findings are... [report.pdf p.3]"
11. state.final_answer = "The key findings are..."

3. UI renders final_answer + debug panel
```

### 5.3 Query with Reformulation (no relevant docs found)

```
[route_after_grading]
→ No score ≥ 0.7 AND iteration_count=0 → reformulate_query

[Node: reformulate_query]
→ gpt-4o-mini("Original: What are the key findings? Best fail reason: ...")
→ reformulated_query = "Summarise the main conclusions of the study"
→ iteration_count = 1

[Node: retrieve again]
→ similarity_search with reformulated_query

[Node: grade_documents again]
→ score=0.82 → passes → generate

  OR if still no pass AND iteration_count=2:

[Node: not_found]
→ "I couldn't find relevant information. (Best score: 0.41 — reason: '...')"
```

---

## 6. Deployment Architecture

### Local Development

```
streamlit run app.py
         │
         ├── app reads .env for OPENAI_API_KEY, CHROMA_PERSIST_DIR
         ├── ChromaDB runs embedded in ./chroma_db/
         └── Phoenix (optional): python -m phoenix.server.main serve
```

### Streamlit Cloud

```
GitHub push to master
      │
      ▼
Streamlit Cloud pulls repo
      │
      ├── pip install -r requirements.txt
      ├── reads OPENAI_API_KEY from st.secrets
      ├── ChromaDB runs embedded in /mount/src/{repo}/chroma_db/
      └── Phoenix unavailable → observability silently skipped
```

**Environment variables:**

| Variable | Default | Required |
|---|---|---|
| `OPENAI_API_KEY` | — | Yes |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | No |
| `PHOENIX_PORT` | `6006` | No |

---

## 7. Multi-User Isolation — Design Rationale

The original architecture used a single shared Chroma collection (`crag_corpus`). This meant:
- User A uploads `finance.pdf` → stored in `crag_corpus`
- User B uploads `medicine.pdf` → stored in `crag_corpus`
- User B asks a medical question → might retrieve chunks from `finance.pdf`

**Solution chosen: per-user Chroma collection**

The alternative (metadata filtering with `user_id`) would work but adds query overhead and has a risk of filter bugs leaking cross-user data. Separate collections give hard isolation at the storage layer with zero risk of accidental cross-contamination.

**Naming convention:** `crag_{slugified_name}`
- "Alice" → `crag_alice`
- "John Doe" → `crag_john_doe`
- "Müller" → `crag_m_ller`

**Trade-off:** Multiple Chroma collections use more disk. For the use case (local dev + Streamlit Cloud with small user counts), this is acceptable. A production deployment with thousands of users would use a vector DB with native namespace/tenant support (e.g. Weaviate, Pinecone namespaces, Qdrant collections).

---

## 8. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **State machine** | LangGraph TypedDict state | Simple dict merge contract; no Pydantic mutations breaking node contracts |
| **Grading model** | `gpt-4o-mini` | Cost-optimised for per-chunk scoring (up to 5 calls per query) |
| **Generation model** | `gpt-4o` | Quality-optimised; only called once per successful query |
| **Relevance threshold** | 0.7 | Empirically reasonable; surfaced in UI so users can see why docs passed/failed |
| **Max reformulations** | 2 | Limits cost; most retrieval failures resolve in 1 reformulation or not at all |
| **Chunk size** | 1000 chars / 200 overlap | Standard RAG default; balances context richness vs retrieval precision |
| **Dedup strategy** | SHA256 of raw bytes | Content-based, not filename-based; survives renames |
| **Lazy node init** | `nonlocal` singletons | Graph compilation is pure Python; no TypeError from package API changes at build time |
| **User identity** | Name input (no auth) | Lightweight for a portfolio/demo; production would use OAuth/JWT |

---

## 9. File Structure

```
rag-project-scaffold/
│
├── app.py                    # Streamlit UI — entry point
├── ingest.py                 # PDF ingestion pipeline
├── observability.py          # Arize Phoenix + LangChain tracing
├── eval.py                   # Ragas offline evaluation
│
├── graph/
│   ├── state.py              # CRAGState + GradeResult TypedDicts
│   ├── nodes.py              # make_nodes(collection_name) factory
│   └── graph.py              # build_graph(collection_name) compiler
│
├── tests/
│   ├── test_ingest.py        # Dedup, chunking, error handling, env config
│   ├── test_graph.py         # Node unit tests (LLMs mocked)
│   ├── test_app.py           # UI smoke tests
│   ├── test_eval.py          # Eval pipeline tests
│   └── test_observability.py # Observability tests
│
├── data/
│   ├── uploads/              # User-uploaded PDFs (gitignored)
│   └── golden_dataset.json   # Ragas test set (gitignored, generated on first run)
│
├── chroma_db/                # ChromaDB persistent storage (gitignored)
├── phoenix_traces/           # OpenTelemetry traces (gitignored)
│
├── requirements.txt
├── .env.example
└── HLD.md                    # This document
```

---

## 10. Limitations & Future Improvements

| Limitation | Potential Fix |
|---|---|
| User identity is name-only (no auth) | Add OAuth via `streamlit-oauth` or a proper auth layer |
| No chat history — each query is stateless | Add `messages: list` to `CRAGState`, thread prior Q&A as context |
| ChromaDB is single-node local | Migrate to a hosted vector DB (Pinecone, Weaviate, Qdrant Cloud) for production |
| Name lost on page refresh | Persist session via URL query params or a cookie |
| `eval.py` uses shared `crag_corpus`, not per-user collections | Pass `collection_name` to eval pipeline |
| No rate limiting or token budget per user | Add per-user usage tracking |
| No document management UI | Allow users to list and delete their ingested documents |
