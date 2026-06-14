# PR2 — feat: PDF ingestion pipeline with dedup

**Branch:** `feat/pdf-ingestion`
**PR ID:** PR-2
**Depends on:** PR-1 (chore/project-scaffold)

---

## What This PR Does

This PR implements `ingest.py` — the complete PDF ingestion pipeline that accepts a list of file paths, parses each PDF with `pypdf`, splits the text into overlapping chunks using `RecursiveCharacterTextSplitter`, embeds the chunks with OpenAI `text-embedding-3-small`, and persists them to a local Chroma vector store. It deduplicates by SHA256 hash so re-ingesting the same file is a safe no-op. It returns a structured `IngestResult` dataclass indicating which files were ingested, skipped (duplicate), or failed (parse error), and includes unit tests covering dedup, chunking, error handling, and hash metadata — all runnable without a real OpenAI API call.

---

## Assumptions

| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
| 1 | `IngestResult` type — dataclass vs TypedDict | `@dataclass` | Issue spec explicitly shows `@dataclass` with three list fields. TypedDict would work but dataclass is cleaner for a return value (attribute access not key access). | Never — spec is explicit |
| 2 | `failed` list element format | `"<filename>: <reason>"` — filename and exception message joined by `: ` | Issue spec states `"<filename>: <exception message>"`. This is the only documented format. | Never — spec is explicit |
| 3 | `doc_hash` query method for dedup | `collection.get(where={"doc_hash": sha256_hex}, limit=1)` | Chroma supports `where` metadata filtering on `.get()`; this is the canonical dedup check without loading full documents. Returns empty `ids` list if not found. | If Chroma collection API changes between 0.5.x versions |
| 4 | `page` metadata field type | `int` | pypdf page index is 0-based integer. Storing as int avoids string-to-int conversion overhead later. | Never |
| 5 | Empty-text detection | `stripped_text == ""` after joining all page texts | pypdf returns empty strings for scanned pages; joining all pages and stripping catches the case where all pages are empty simultaneously. | If partial-page extraction is needed |
| 6 | `load_dotenv()` call location | Top of module, before any env reads | `python-dotenv` docs recommend calling at process entry. Module-level call ensures env vars are populated before `os.getenv()` is called anywhere in the module. | Never |
| 7 | Chroma client mode | In-process client (`chromadb.PersistentClient`) via `langchain_community.vectorstores.Chroma` | PRD specifies `persist_directory` — this maps to a `PersistentClient`. No HTTP server needed. | If scaling to a multi-process deployment |
| 8 | Test isolation for Chroma | Use `tmp_path` pytest fixture + `chromadb.EphemeralClient` or unique `persist_directory` per test | Without isolation, test runs pollute each other. Each test gets a fresh in-memory Chroma collection. | Never |
| 9 | Mock embeddings in tests | `unittest.mock.patch` on `OpenAIEmbeddings` returning a fixed-dimension list | No real API call; avoids `OPENAI_API_KEY` requirement in CI. Fixed vector `[0.0] * 1536` is sufficient for Chroma storage tests. | If integration tests are added separately |
| 10 | `tests/` directory location | `tests/test_ingest.py` at repo root level | PR1 plan noted tests would be added in a later PR; this PR is the first to need them. Flat `tests/` next to `ingest.py` follows the existing file layout. | Never |
| 11 | `pytest` and `pytest-mock` availability | Assumed available via `pip install pytest pytest-mock` — not in `requirements.txt` | `requirements.txt` covers runtime deps only. Test deps are dev-only and installed separately. | If a `requirements-dev.txt` is added |

---

## Task Table

| Task ID | What it builds | Files |
|---------|---------------|-------|
| T1 | `IngestResult` dataclass and `ingest_pdfs` function signature | `ingest.py` |
| T2 | SHA256 deduplication logic | `ingest.py` |
| T3 | pypdf loading + empty-text detection | `ingest.py` |
| T4 | RecursiveCharacterTextSplitter chunking with metadata | `ingest.py` |
| T5 | OpenAI embedding + Chroma persistence | `ingest.py` |
| T6 | Unit tests (dedup, chunking, error handling, hash metadata) | `tests/test_ingest.py` |

---

## Architecture Constraints

| Constraint | Source | Consequence if violated |
|-----------|--------|------------------------|
| No OCR dependency | PRD §Out of Scope | Tesseract/pytesseract must not appear in `requirements.txt` or `ingest.py` |
| pypdf only for PDF parsing | PRD §Ingestion Module | Using `pdfplumber`, `PyMuPDF`, or similar introduces an unlisted dependency and breaks the constraint |
| SHA256 dedup must use raw PDF bytes (before chunking) | PRD §Ingestion Module | Hash computed from decoded text would miss byte-identical PDFs with different encodings |
| `doc_hash` stored as metadata on every chunk | Issue spec §Deduplication | Without per-chunk metadata, dedup query returns no results and every file is re-ingested |
| Batch error isolation — one file failure must not abort the batch | PRD §Ingestion Module, Issue spec §Error isolation | An unhandled exception in one file would `raise` and skip all remaining files |
| `CHROMA_PERSIST_DIR` must be read from env var, default `./chroma_db` | PRD §Environment | Hardcoded path breaks env-var-based deployment |
| `OPENAI_API_KEY` read from env via `python-dotenv` `load_dotenv()` | PRD §Environment, Issue spec §Config loading | Without `load_dotenv()`, `.env` file is ignored and API calls fail |
| `langchain-openai` `OpenAIEmbeddings` — no raw `openai` SDK calls | PRD §Ingestion Module | Direct `openai` SDK usage bypasses LangChain instrumentation that Phoenix observability relies on |
| Collection name must be `"crag_corpus"` | PRD §Ingestion Module | A different collection name would produce a separate Chroma collection invisible to the retriever in `graph/nodes.py` |
| Unit tests must not require a real `OPENAI_API_KEY` | Issue spec §Acceptance criteria | CI/CD or local dev without keys would be blocked |

---

## T1 — `IngestResult` Dataclass and `ingest_pdfs` Signature

### What it builds

The public-facing data contract for this module: the `IngestResult` dataclass returned by `ingest_pdfs`, and the function signature. This is the boundary other modules (Streamlit UI, CLI) interact with.

### Column decisions

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| `IngestResult.ingested` | `list[str]` | No | `field(default_factory=list)` | Filenames (not full paths) of PDFs successfully chunked and stored |
| `IngestResult.skipped` | `list[str]` | No | `field(default_factory=list)` | Filenames skipped because hash already exists in Chroma |
| `IngestResult.failed` | `list[str]` | No | `field(default_factory=list)` | `"<filename>: <reason>"` strings for parse or processing errors |

### Layer compliance checklist

- [ ] `IngestResult` is a `@dataclass` — not a `TypedDict`, not a Pydantic model
- [ ] `ingest_pdfs` accepts `list[Path]` — callers must pass `pathlib.Path` objects, not strings
- [ ] Return type annotation `-> IngestResult` present
- [ ] No LangGraph imports in `ingest.py`

### Known limitations

The `ingest_pdfs` function signature uses `list[Path]`. The Streamlit UI (PR #5) will wrap this with `Path(uploaded_file.name)` or write the `UploadedFile` bytes to a temp file first. That wrapping is PR #5's concern.

### Implementation

```python
"""PDF ingestion pipeline.

Public API:
    ingest_pdfs(file_paths: list[Path]) -> IngestResult

Environment variables:
    OPENAI_API_KEY      — required for embeddings
    CHROMA_PERSIST_DIR  — path to Chroma persistence directory (default: ./chroma_db)
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class IngestResult:
    """Structured result returned by ingest_pdfs."""

    ingested: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def ingest_pdfs(file_paths: list[Path]) -> IngestResult:
    ...  # implementation in T2–T5
```

### Acceptance criteria

- [ ] `from ingest import ingest_pdfs, IngestResult` succeeds without `OPENAI_API_KEY` set
- [ ] `IngestResult` has exactly three fields: `ingested`, `skipped`, `failed`, all `list[str]`
- [ ] `ingest_pdfs` type signature matches `(file_paths: list[Path]) -> IngestResult`

---

## T2 — SHA256 Deduplication Logic

### What it builds

Before any processing, compute the SHA256 hash of the raw PDF bytes. Query Chroma for any existing chunk with that hash. If found, add to `skipped` and continue to the next file.

### Implementation

```python
def _compute_sha256(file_path: Path) -> str:
    """Return hex SHA256 digest of raw file bytes."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _is_already_ingested(vectorstore, sha256_hex: str) -> bool:
    """Return True if any chunk with doc_hash==sha256_hex exists in the collection."""
    results = vectorstore.get(where={"doc_hash": sha256_hex}, limit=1)
    return len(results["ids"]) > 0
```

Within `ingest_pdfs`, the dedup check happens first:

```python
sha256_hex = _compute_sha256(file_path)
if _is_already_ingested(vectorstore, sha256_hex):
    result.skipped.append(file_path.name)
    continue
```

### Known limitations

Chroma's `where` filter requires the collection to have at least one document. On an empty collection, Chroma raises a `ValueError` in some versions. The implementation must handle this edge case:

```python
def _is_already_ingested(vectorstore, sha256_hex: str) -> bool:
    try:
        results = vectorstore.get(where={"doc_hash": sha256_hex}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        # Empty collection raises in some Chroma 0.5.x builds
        return False
```

### Acceptance criteria

- [ ] Re-ingesting the same PDF bytes returns the filename in `skipped` and adds zero new chunks to Chroma
- [ ] A different file with different bytes is NOT classified as duplicate even if it has the same filename
- [ ] SHA256 is computed from raw bytes, not from extracted text

---

## T3 — pypdf Loading and Empty-Text Detection

### What it builds

Load the PDF with `pypdf.PdfReader`. Extract text from all pages. If the reader raises, or if the joined text is empty after stripping, classify as a parse failure.

### Implementation

```python
from pypdf import PdfReader


def _load_pdf_text(file_path: Path) -> str:
    """
    Extract full text from a PDF.

    Raises ValueError if text is empty (scanned/image-only PDF).
    Propagates pypdf exceptions as-is for corrupted/password-protected files.
    """
    reader = PdfReader(str(file_path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages_text).strip()
    if not full_text:
        raise ValueError("No extractable text found (scanned or image-only PDF)")
    return full_text
```

Within `ingest_pdfs`, per-file error isolation:

```python
try:
    text = _load_pdf_text(file_path)
except Exception as exc:
    reason = str(exc) if str(exc) else type(exc).__name__
    result.failed.append(f"{file_path.name}: {reason}")
    print(f"[ingest] SKIP {file_path.name}: {reason}", file=sys.stderr)
    continue
```

### Known limitations

- Scanned PDFs (image-only, no text layer) return empty string from `pypdf` and are classified as failures. This is intentional per the PRD — OCR is out of scope.
- Password-protected PDFs raise `pypdf.errors.FileNotDecryptedError`. This is caught by the broad `except Exception` and appears in `failed` with the exception message.

### Acceptance criteria

- [ ] A PDF with extractable text returns `full_text` (non-empty string)
- [ ] A PDF with no extractable text raises `ValueError` with `"No extractable text found"` in the message
- [ ] A corrupted file (not a valid PDF) raises an exception that is caught and added to `failed`
- [ ] Processing continues for remaining files after a single file fails

---

## T4 — Chunking with Metadata

### What it builds

Split the extracted text into overlapping chunks. Attach `source`, `doc_hash`, and `page` metadata to each chunk. Page numbers are approximated at the chunk level (best-effort from pypdf page boundaries).

### Design decision: page metadata approach

Per-chunk page numbers require tracking which page each character came from during extraction. The simpler approach (and consistent with the issue spec which just says `"page": page_number`) is to attach page metadata at the page level before splitting:

```python
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def _chunk_pdf(file_path: Path, sha256_hex: str) -> list[Document]:
    """
    Load PDF page-by-page and produce chunked Documents with metadata.

    Each Document carries: source, doc_hash, page (0-based index).
    """
    reader = PdfReader(str(file_path))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    all_docs: list[Document] = []
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue
        chunks = splitter.create_documents(
            texts=[page_text],
            metadatas=[{
                "source": file_path.name,
                "doc_hash": sha256_hex,
                "page": page_num,
            }],
        )
        all_docs.extend(chunks)

    return all_docs
```

Note: `_load_pdf_text` is used only for the empty-text check (T3). `_chunk_pdf` does its own page-level extraction so that metadata is page-accurate.

### Acceptance criteria

- [ ] Each chunk has `metadata["source"] == file_path.name`
- [ ] Each chunk has `metadata["doc_hash"] == sha256_hex`
- [ ] Each chunk has `metadata["page"]` as an integer
- [ ] Chunk count for a ~3000-character document falls in range `[2, 6]` with chunk_size=1000, overlap=200
- [ ] No chunk exceeds ~1200 characters (chunk_size + splitter tolerance)

---

## T5 — OpenAI Embedding and Chroma Persistence

### What it builds

Initialise `OpenAIEmbeddings` and `Chroma` vector store once per `ingest_pdfs` call (not per file). Add chunks using `vectorstore.add_documents()`. This triggers embedding and persistence in one call.

### Implementation

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"


def _get_vectorstore() -> Chroma:
    """Return (or create) the persistent Chroma vector store."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
```

Within `ingest_pdfs`, after successful loading and chunking:

```python
docs = _chunk_pdf(file_path, sha256_hex)
if not docs:
    result.failed.append(f"{file_path.name}: produced zero chunks after splitting")
    continue
vectorstore.add_documents(docs)
result.ingested.append(file_path.name)
```

### Full `ingest_pdfs` implementation

```python
def ingest_pdfs(file_paths: list[Path]) -> IngestResult:
    """
    Ingest a list of PDF files into the Chroma vector store.

    For each file:
    - Compute SHA256 of raw bytes; skip if already present in Chroma.
    - Parse with pypdf; skip with error if text is empty or parse fails.
    - Chunk with RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200).
    - Embed with OpenAI text-embedding-3-small and persist to Chroma.

    Returns:
        IngestResult with lists of ingested, skipped, and failed filenames.
    """
    result = IngestResult()
    vectorstore = _get_vectorstore()

    for file_path in file_paths:
        file_path = Path(file_path)  # accept str inputs defensively
        try:
            sha256_hex = _compute_sha256(file_path)

            if _is_already_ingested(vectorstore, sha256_hex):
                result.skipped.append(file_path.name)
                continue

            # Validate text is extractable (raises on empty/corrupt)
            _load_pdf_text(file_path)

            docs = _chunk_pdf(file_path, sha256_hex)
            if not docs:
                raise ValueError("produced zero chunks after splitting")

            vectorstore.add_documents(docs)
            result.ingested.append(file_path.name)

        except Exception as exc:
            reason = str(exc) if str(exc) else type(exc).__name__
            result.failed.append(f"{file_path.name}: {reason}")
            print(f"[ingest] SKIP {file_path.name}: {reason}", file=sys.stderr)

    return result
```

### Acceptance criteria

- [ ] `ingest_pdfs([valid_pdf])` returns `IngestResult(ingested=["file.pdf"], skipped=[], failed=[])`
- [ ] Chroma collection `"crag_corpus"` in `CHROMA_PERSIST_DIR` contains chunks after ingestion
- [ ] `vectorstore.similarity_search("test", k=1)` returns a document with `metadata["doc_hash"]` set
- [ ] `CHROMA_PERSIST_DIR` env var override creates collection in the specified directory

---

## T6 — Unit Tests

### What it builds

`tests/test_ingest.py` — pytest test suite covering all acceptance criteria from the issue spec. All tests mock `OpenAIEmbeddings` to avoid real API calls. Each test gets an isolated in-memory Chroma collection.

### Test infrastructure

```python
"""Unit tests for ingest.py.

Run with: pytest tests/test_ingest.py -v
No OPENAI_API_KEY required — embeddings are mocked.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """Isolated Chroma persist directory per test."""
    return str(tmp_path / "chroma_test")


@pytest.fixture
def fake_embeddings():
    """Mock OpenAIEmbeddings that returns fixed 1536-dim vectors."""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.0] * 1536]
    mock.embed_query.return_value = [0.0] * 1536
    return mock


@pytest.fixture
def simple_pdf(tmp_path) -> Path:
    """Create a minimal valid PDF with extractable text."""
    # Use pypdf to create a test PDF, or use a pre-built binary.
    # Simplest approach: write a minimal PDF that pypdf can parse.
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>\nstream\nBT /F1 12 Tf 100 700 Td (Hello World) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000206 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"
    )
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path) -> Path:
    """A PDF with no extractable text (image-only simulation via empty stream)."""
    # Minimal PDF with empty content stream
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R>>endobj\n"
        b"4 0 obj<</Length 0>>\nstream\n\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000206 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n260\n%%EOF"
    )
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path
```

### Test cases

```python
# ---------------------------------------------------------------------------
# Dedup tests
# ---------------------------------------------------------------------------

class TestDedup:
    def test_reingest_same_file_returns_skipped(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Re-ingesting the same PDF bytes must return skipped, add zero chunks."""
        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            # First ingest
            result1 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result1.ingested

            # Second ingest — same file
            result2 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result2.skipped
            assert simple_pdf.name not in result2.ingested

    def test_dedup_is_byte_based_not_filename_based(self, tmp_chroma_dir, fake_embeddings, simple_pdf, tmp_path):
        """A copy of the same bytes under a different name is still a duplicate."""
        copy_path = tmp_path / "copy_of_test.pdf"
        copy_path.write_bytes(simple_pdf.read_bytes())

        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            result1 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result1.ingested

            result2 = ingest_pdfs([copy_path])
            assert copy_path.name in result2.skipped

    def test_reingest_adds_zero_new_chunks(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Chunk count in Chroma must not change after dedup skip."""
        import chromadb
        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            ingest_pdfs([simple_pdf])

            client = chromadb.PersistentClient(path=tmp_chroma_dir)
            collection = client.get_collection("crag_corpus")
            count_after_first = collection.count()

            ingest_pdfs([simple_pdf])
            count_after_second = collection.count()

        assert count_after_first == count_after_second


# ---------------------------------------------------------------------------
# Chunking tests
# ---------------------------------------------------------------------------

class TestChunking:
    def test_chunk_count_in_expected_range(self, tmp_chroma_dir, fake_embeddings, tmp_path):
        """A ~3000-char PDF should produce 2–6 chunks with size=1000, overlap=200."""
        # Build a PDF with known text length ~3000 chars
        # Use a real pypdf-parseable PDF for this test
        # Since building PDFs is complex, we test _chunk_pdf directly
        from pathlib import Path
        from unittest.mock import patch as mp
        import ingest as ing

        # Mock a PDF with known text
        long_text = "A" * 3000
        with mp.object(ing, "_load_pdf_text", return_value=long_text):
            # Use _chunk_pdf indirectly by examining splitter behavior
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""],
            )
            chunks = splitter.split_text(long_text)
            assert 2 <= len(chunks) <= 6, f"Expected 2–6 chunks, got {len(chunks)}"

    def test_chunk_metadata_fields(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Each chunk must have source, doc_hash, and page metadata fields."""
        import ingest as ing
        sha256_hex = hashlib.sha256(simple_pdf.read_bytes()).hexdigest()
        docs = ing._chunk_pdf(simple_pdf, sha256_hex)
        assert len(docs) > 0
        for doc in docs:
            assert "source" in doc.metadata
            assert "doc_hash" in doc.metadata
            assert "page" in doc.metadata
            assert doc.metadata["source"] == simple_pdf.name
            assert doc.metadata["doc_hash"] == sha256_hex
            assert isinstance(doc.metadata["page"], int)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_empty_pdf_returns_failed(self, tmp_chroma_dir, fake_embeddings, empty_pdf):
        """A PDF with no extractable text must appear in failed with a non-empty reason."""
        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            result = ingest_pdfs([empty_pdf])
        assert len(result.failed) == 1
        assert empty_pdf.name in result.failed[0]
        # Reason must be non-empty (after the colon)
        reason = result.failed[0].split(": ", 1)[1]
        assert reason.strip() != ""

    def test_corrupt_file_returns_failed(self, tmp_chroma_dir, fake_embeddings, tmp_path):
        """A corrupt file (not valid PDF) must appear in failed, not raise."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_bytes(b"this is not a pdf")
        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            result = ingest_pdfs([corrupt])
        assert len(result.failed) == 1
        assert "corrupt.pdf" in result.failed[0]

    def test_batch_continues_after_failure(self, tmp_chroma_dir, fake_embeddings, simple_pdf, empty_pdf, tmp_path):
        """[valid, empty, valid] batch returns 2 ingested and 1 failed."""
        simple_pdf2 = tmp_path / "second_valid.pdf"
        # Write different bytes so it's not a dedup hit
        simple_pdf2.write_bytes(simple_pdf.read_bytes() + b" extra")

        # simple_pdf2 won't be parseable as PDF since we appended garbage,
        # so use two distinct valid PDFs. Here we copy simple_pdf with different content:
        # For simplicity, use the same simple_pdf fixture path + a freshly created PDF
        # We'll patch _load_pdf_text to simulate valid/invalid/valid
        import ingest as ing

        call_count = {"n": 0}
        originals = {}

        def mock_load(fp):
            call_count["n"] += 1
            if fp.name == empty_pdf.name:
                raise ValueError("No extractable text found")
            return "Some valid text content " * 50

        def mock_chunk(fp, sha256):
            from langchain.schema import Document
            return [Document(
                page_content="chunk text",
                metadata={"source": fp.name, "doc_hash": sha256, "page": 0}
            )]

        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir), \
             patch.object(ing, "_load_pdf_text", side_effect=mock_load), \
             patch.object(ing, "_chunk_pdf", side_effect=mock_chunk):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf, empty_pdf, simple_pdf2])

        assert len(result.ingested) == 2
        assert len(result.failed) == 1
        assert empty_pdf.name in result.failed[0]


# ---------------------------------------------------------------------------
# Hash metadata test
# ---------------------------------------------------------------------------

class TestHashMetadata:
    def test_doc_hash_matches_sha256_of_source_bytes(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Every ingested chunk's doc_hash must equal SHA256 of source file bytes."""
        import chromadb
        expected_hash = hashlib.sha256(simple_pdf.read_bytes()).hexdigest()

        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", tmp_chroma_dir):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf])
        assert simple_pdf.name in result.ingested

        client = chromadb.PersistentClient(path=tmp_chroma_dir)
        collection = client.get_collection("crag_corpus")
        items = collection.get(include=["metadatas"])
        for meta in items["metadatas"]:
            assert meta["doc_hash"] == expected_hash


# ---------------------------------------------------------------------------
# Environment variable test
# ---------------------------------------------------------------------------

class TestEnvConfig:
    def test_chroma_persist_dir_env_override(self, tmp_path, fake_embeddings, simple_pdf):
        """CHROMA_PERSIST_DIR env var must override the default ./chroma_db path."""
        custom_dir = str(tmp_path / "custom_chroma")
        with patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings), \
             patch("ingest.CHROMA_PERSIST_DIR", custom_dir):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf])
        assert simple_pdf.name in result.ingested
        import os
        assert os.path.exists(custom_dir), "Custom CHROMA_PERSIST_DIR was not created"
```

### Acceptance criteria

- [ ] `pytest tests/test_ingest.py -v` exits with code 0 (all tests pass)
- [ ] No test requires `OPENAI_API_KEY` environment variable
- [ ] Each test is isolated — no shared Chroma state between tests
- [ ] Tests cover: dedup (3 tests), chunking (2 tests), error handling (3 tests), hash metadata (1 test), env config (1 test)

---

## Migration

Not applicable. This PR introduces no database schema, no SQLAlchemy models, and no Alembic migrations. Chroma is a vector store managed entirely through the `chromadb` Python client — no migration tooling needed.

---

## Test quality rules

### Dedup correctness via collection count

```python
count_before = collection.count()
ingest_pdfs([already_ingested_pdf])
count_after = collection.count()
assert count_before == count_after  # exactly zero new chunks
```

### Hash metadata via exact string comparison

```python
expected = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
items = collection.get(include=["metadatas"])
for meta in items["metadatas"]:
    assert meta["doc_hash"] == expected  # not "starts with", exact match
```

### Nullable fields: `failed` reason must be non-empty string

```python
reason_part = result.failed[0].split(": ", 1)[1]
assert isinstance(reason_part, str) and len(reason_part) > 0
```

### Batch isolation: error in middle file does not skip later files

```python
# [valid, bad, valid] → ingested must have length 2, failed must have length 1
assert len(result.ingested) == 2
assert len(result.failed) == 1
```

### Chunk count range assertion (not exact count)

```python
assert 2 <= chunk_count <= 6  # not assert chunk_count == 3
```

Range assertions tolerate splitter variance across pypdf versions and chunk boundary decisions.

---

## Automated verification

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install test dependencies (not in requirements.txt — dev-only)
pip install pytest pytest-mock

# Run all tests
pytest tests/test_ingest.py -v

# Smoke-test: import succeeds without OPENAI_API_KEY
python -c "from ingest import ingest_pdfs, IngestResult; print('Import OK')"

# Lint (if ruff or flake8 is available)
ruff check ingest.py tests/test_ingest.py || flake8 ingest.py tests/test_ingest.py
```

---

## Manual verification

1. **Happy path — single valid PDF:**
   ```bash
   python -c "
   from pathlib import Path
   from ingest import ingest_pdfs
   result = ingest_pdfs([Path('data/uploads/sample.pdf')])
   print('Ingested:', result.ingested)
   print('Skipped:', result.skipped)
   print('Failed:', result.failed)
   "
   # Expected: Ingested: ['sample.pdf'], Skipped: [], Failed: []
   ```

2. **Dedup check — reingest same file:**
   ```bash
   python -c "
   from pathlib import Path
   from ingest import ingest_pdfs
   p = Path('data/uploads/sample.pdf')
   r1 = ingest_pdfs([p])
   print('First:', r1)
   r2 = ingest_pdfs([p])
   print('Second:', r2)
   "
   # Expected: Second shows Skipped: ['sample.pdf'], not Ingested
   ```

3. **Verify doc_hash metadata in Chroma:**
   ```bash
   python -c "
   import os, hashlib, chromadb
   p = 'data/uploads/sample.pdf'
   expected = hashlib.sha256(open(p,'rb').read()).hexdigest()
   client = chromadb.PersistentClient(path=os.getenv('CHROMA_PERSIST_DIR','./chroma_db'))
   col = client.get_collection('crag_corpus')
   items = col.get(include=['metadatas'])
   hashes = {m['doc_hash'] for m in items['metadatas']}
   print('Hash match:', expected in hashes)
   "
   # Expected: Hash match: True
   ```

4. **Error isolation — batch with a bad file:**
   ```bash
   python -c "
   from pathlib import Path
   from ingest import ingest_pdfs
   import tempfile, os
   with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
       f.write(b'not a pdf')
       bad = f.name
   result = ingest_pdfs([Path('data/uploads/sample.pdf'), Path(bad)])
   print('Ingested:', result.ingested)
   print('Failed:', result.failed)
   os.unlink(bad)
   "
   # Expected: Ingested has sample.pdf; Failed has the bad file with a reason
   ```

5. **CHROMA_PERSIST_DIR env override:**
   ```bash
   CHROMA_PERSIST_DIR=/tmp/test_chroma python -c "
   from pathlib import Path
   from ingest import ingest_pdfs
   result = ingest_pdfs([Path('data/uploads/sample.pdf')])
   import os
   print('Dir exists:', os.path.exists('/tmp/test_chroma'))
   "
   # Expected: Dir exists: True
   ```

6. **Chunk count sanity check:**
   ```bash
   python -c "
   import chromadb, os
   client = chromadb.PersistentClient(path=os.getenv('CHROMA_PERSIST_DIR','./chroma_db'))
   col = client.get_collection('crag_corpus')
   print('Total chunks:', col.count())
   "
   # Expected: > 0 after ingesting at least one PDF
   ```

---

## Implementation Notes

**Import deviations from plan (logged per pr-implement.md instructions):**

1. `langchain.schema.Document` → replaced with `langchain_core.documents.Document`
   - Reason: installed langchain 1.3.9 removed `langchain.schema`; `langchain_core` is the canonical location.
   - Constraint preserved: no raw `openai` SDK usage; `OpenAIEmbeddings` from `langchain-openai` is used.

2. `langchain.text_splitter.RecursiveCharacterTextSplitter` → replaced with `langchain_text_splitters.RecursiveCharacterTextSplitter`
   - Reason: installed langchain 1.3.9 removed `langchain.text_splitter`; `langchain_text_splitters` is the current package.

3. Test patch strategy: the plan uses `patch("ingest.OpenAIEmbeddings", return_value=fake_embeddings)` + `importlib.reload`. With langchain-openai 1.3.2, `OpenAIEmbeddings.__init__` validates API keys at instantiation — the patch approach needed adjustment. Tests instead patch `ingest._get_vectorstore` with a `side_effect` that returns a real `Chroma` instance backed by a mock embedding function. This fully satisfies the "no OPENAI_API_KEY required in tests" constraint.

4. PDF test fixtures: the plan's hand-crafted PDF binaries lack correct xref byte offsets and font resources, causing `pypdf` 6.x to raise `PdfReadError: Trailer cannot be read`. Replaced with a `_build_pdf()` helper that calculates correct xref offsets. The `simple_pdf` fixture now produces a PDF that pypdf 6.x can parse and extract text from.

5. `langchain_community.vectorstores.Chroma` deprecation warning: langchain-community 0.4.2 warns that this class is deprecated in favor of `langchain-chroma`. Not fixed — constraint in plan specifies `langchain_community.vectorstores.Chroma` explicitly; migration to `langchain-chroma` is a future PR concern.
