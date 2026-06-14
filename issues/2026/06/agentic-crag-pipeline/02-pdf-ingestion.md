# feat: PDF ingestion pipeline with dedup

> Issue #2 | Branch `feat/pdf-ingestion` | Type AFK
> Depends on: #1
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Implement `ingest.py` — the full PDF ingestion pipeline. It accepts a list of file paths, loads each PDF with pypdf, splits the text into chunks, embeds the chunks with OpenAI, and persists them to a local Chroma collection. It deduplicates by SHA256 hash so re-ingesting the same file is a no-op. It returns a structured result indicating which files were ingested, skipped (duplicate), or failed (parse error). Include unit tests for dedup, chunking output, error handling, and hash metadata.

## Resolved decisions

**Public interface:**
```python
def ingest_pdfs(file_paths: list[Path]) -> IngestResult:
    ...

@dataclass
class IngestResult:
    ingested: list[str]   # filenames successfully ingested
    skipped: list[str]    # filenames skipped (already in Chroma)
    failed: list[str]     # filenames that failed, with reason appended
```

**Deduplication:**
- Compute SHA256 of raw PDF bytes before any processing
- Query Chroma collection for any existing chunk with metadata field `doc_hash` == computed hash
- If found: add filename to `skipped`, do not re-ingest, return immediately for that file
- Store `doc_hash` as a metadata field on every chunk ingested from that file

**PDF loading:** `pypdf.PdfReader`. If `PdfReader` raises or extracted text across all pages is empty string after strip, classify as a parse failure. Add `"<filename>: <exception message>"` to `failed`. Continue processing remaining files.

**Chunking:** `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`. Separators: `["\n\n", "\n", " ", ""]` (default). Each chunk carries metadata: `{ "source": filename, "doc_hash": sha256_hex, "page": page_number }`.

**Embedding:** `OpenAIEmbeddings(model="text-embedding-3-small")` from `langchain-openai`. API key read from `OPENAI_API_KEY` env var.

**Vector store:** `Chroma(collection_name="crag_corpus", persist_directory=CHROMA_PERSIST_DIR)`. `CHROMA_PERSIST_DIR` read from env var, defaults to `./chroma_db`.

**Config loading:** Use `python-dotenv` `load_dotenv()` at module import time to populate env vars from `.env`.

**Error isolation:** A single file's failure must never raise an exception that aborts the batch. Catch all exceptions per file, log to stderr, append to `failed`.

## Acceptance criteria

- [ ] Ingesting a valid PDF returns the filename in `IngestResult.ingested` and adds chunks to Chroma
- [ ] Re-ingesting the same PDF returns the filename in `IngestResult.skipped` and adds zero new chunks to Chroma
- [ ] Each ingested chunk has a `doc_hash` metadata field equal to the SHA256 hex of the source file bytes
- [ ] Ingesting a file with no extractable text returns the filename in `IngestResult.failed` with a non-empty reason string
- [ ] A batch of [valid PDF, empty PDF, valid PDF] returns 2 ingested and 1 failed — the batch does not abort on the failing file
- [ ] Chunk count for a known-length PDF falls within the expected range for chunk_size=1000, overlap=200
- [ ] `CHROMA_PERSIST_DIR` env var overrides the default `./chroma_db` path
- [ ] Unit tests pass for all of the above without requiring a real OpenAI API call (mock embeddings)

## Out of scope

- Streamlit upload UI — that is issue #5
- OCR fallback for scanned PDFs — explicitly out of scope for the entire project
- Any format other than PDF
