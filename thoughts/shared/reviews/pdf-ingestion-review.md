# PR Review — feat/pdf-ingestion (PR-2)

**Branch:** `feat/pdf-ingestion`
**Plan:** `thoughts/shared/plans/PR2-pdf-ingestion.md`
**Reviewer:** Claude Code (automated multi-perspective review)
**Date:** 2026-06-14

---

## Plan Alignment

The plan file `PR2-pdf-ingestion.md` was read in full before this review. The implementation is judged against the plan's stated acceptance criteria, architecture constraints, and known limitations.

---

## 1. Critical — must fix before merging

No critical issues found.

---

## 2. Important — should fix

### I1. `requirements.txt` pins `pypdf==4.*` but installed/tested version is pypdf 6.x

**File:** `requirements.txt`, line 10  
**Observed:** `pypdf==4.*` is pinned in `requirements.txt`, yet the running environment has pypdf 6.13.2 installed, and the test PDF builder helper (`_build_pdf`, `_build_empty_pdf` in `tests/test_ingest.py`) was explicitly redesigned per the plan's Implementation Notes to handle "pypdf 6.x" xref parsing behavior. The plan note states: "Replaced with a `_build_pdf()` helper that calculates correct xref offsets. The `simple_pdf` fixture now produces a PDF that pypdf 6.x can parse." If a developer installs from `requirements.txt` strictly (pypdf 4.x), the PDF fixtures may behave differently and some tests may fail or produce different extraction results. The constraint `pypdf only for PDF parsing` is satisfied, but the version pin does not match actual usage.

**Recommendation:** Update `requirements.txt` to `pypdf>=6.0,<7` to match the version actually tested and documented in the implementation notes.

### I2. `TestEnvConfig.test_chroma_persist_dir_env_override` does not actually test the env var code path

**File:** `tests/test_ingest.py`, lines 340–358  
**Observed:** The test patches `ingest._get_vectorstore` entirely with a `mock_get_vs` function that hardcodes `custom_dir` directly. This means the test validates that Chroma creates a directory when given a path — it does NOT test that the module-level `CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")` reads the env var or that `_get_vectorstore()` uses `CHROMA_PERSIST_DIR`. The plan's acceptance criterion states: "`CHROMA_PERSIST_DIR` env var override creates collection in the specified directory." The actual env-var code path is not exercised. If `CHROMA_PERSIST_DIR` was removed from `_get_vectorstore()`, this test would still pass.

**Recommendation:** The test should either (a) patch `ingest.CHROMA_PERSIST_DIR` directly and not mock `_get_vectorstore`, or (b) set `os.environ["CHROMA_PERSIST_DIR"]` and reload the module, then verify the real `_get_vectorstore()` uses the custom path. The plan's Assumption #6 and constraint `CHROMA_PERSIST_DIR must be read from env var` need a test that exercises the real lookup chain.

### I3. `langchain_text_splitters` missing from `requirements.txt`

**File:** `requirements.txt`  
**Observed:** `ingest.py` imports `from langchain_text_splitters import RecursiveCharacterTextSplitter` and `tests/test_ingest.py` imports from the same package directly. `langchain_text_splitters` is a standalone package (as noted in Implementation Note #2), but it is not listed in `requirements.txt`. It may be pulled in as a transitive dependency of `langchain==0.3.*`, but it is a direct dependency of the module code and should be listed explicitly to prevent breakage if the transitive dependency chain changes.

**Recommendation:** Add `langchain-text-splitters` (or the pinned version used) to `requirements.txt`.

---

## 3. Minor — consider fixing

### M1. PDF read performed twice per file (T3 + T4 redundancy)

**File:** `ingest.py`, lines 138–140  
**Observed:** `_load_pdf_text(file_path)` opens and reads the PDF with `PdfReader` purely to validate text is extractable, then `_chunk_pdf(file_path, sha256_hex)` opens the same PDF a second time with another `PdfReader`. This is a redundant I/O operation. The plan's design note acknowledges this separation ("Note: `_load_pdf_text` is used only for the empty-text check"), so this is a deliberate choice, but it doubles disk I/O for every successfully ingested file.

**Recommendation:** Consider removing the separate `_load_pdf_text` pre-check and letting `_chunk_pdf` handle the zero-chunks case (which already has `if not docs: raise ValueError("produced zero chunks after splitting")`). This is a minor efficiency issue only.

### M2. `langchain_community.vectorstores.Chroma` deprecation warning in tests

**File:** `ingest.py` line 23, `tests/test_ingest.py` line 136  
**Observed:** Both test runs and module import emit a `LangChainDeprecationWarning` that `langchain_community.vectorstores.Chroma` is deprecated and will be removed in LangChain 1.0. The plan's Implementation Note #5 explicitly documents this as a known deviation: "migration to `langchain-chroma` is a future PR concern." This is correctly tracked. The plan constraint explicitly requires `langchain_community.vectorstores.Chroma`, so no change should be made in this PR.

**Note:** Already tracked in the plan. No action needed in this PR.

### M3. Import order in `ingest.py`: third-party imports not PEP 8 ordered after `load_dotenv()` call

**File:** `ingest.py`, lines 18–25  
**Observed:** The `load_dotenv()` call at module level sits between the `from dotenv import load_dotenv` import and the subsequent LangChain imports. While this is functionally necessary (so that env vars are set before `CHROMA_PERSIST_DIR = os.getenv(...)` runs), the `load_dotenv()` statement breaking the import block is unconventional. PEP 8 and the plan's import order rule (stdlib → third-party → `app.*`) is otherwise satisfied, but a reader may be confused by the call in the middle of imports.

**Recommendation:** Add a brief comment explaining why `load_dotenv()` appears here (it already exists in the docstring but not inline). Low priority.

### M4. Test `test_batch_continues_after_failure` uses `ingest_pdfs` re-imported after patching, which may not reflect the patch

**File:** `tests/test_ingest.py`, lines 296–304  
**Observed:** The test does `from ingest import ingest_pdfs` inside the `with patch.object(...)` block. Since `ingest_pdfs` was already imported at the module level in earlier tests (Python caches imports), this re-import returns the already-cached function object — the `patch.object` calls targeting `ing._load_pdf_text` and `ing._chunk_pdf` are on the module object, so the patches do apply correctly to calls within `ingest_pdfs`. No functional bug, but the `from ingest import ingest_pdfs` inside the with-block is misleading — the function reference was already bound by earlier test imports.

---

## 4. Positive findings

### P1. Comprehensive test isolation — all tests use isolated Chroma directories

Every test that touches Chroma uses a fresh `tmp_chroma_dir` (pytest `tmp_path`-based unique directory). No shared state between tests. This is exactly what the plan's Assumption #8 requires and the test quality rules document.

### P2. SHA256 computed from raw bytes before any parsing

`_compute_sha256(file_path)` calls `file_path.read_bytes()` — no decoding, no text extraction. This correctly satisfies the architecture constraint "SHA256 dedup must use raw PDF bytes (before chunking)."

### P3. Error isolation is complete — exception handler wraps the entire per-file block

The `try/except Exception` in `ingest_pdfs` wraps everything from `_compute_sha256` through `vectorstore.add_documents`. Even a failure during SHA256 computation (e.g., file not found) is caught and added to `failed`, ensuring the loop always continues to the next file.

### P4. `from __future__ import annotations` present in both files

Both `ingest.py` (line 10) and `tests/test_ingest.py` (line 4) have `from __future__ import annotations` as the first non-comment line. Satisfies the plan's layer compliance checklist.

### P5. All 10 tests pass without `OPENAI_API_KEY`

Running `pytest tests/test_ingest.py -v` shows 10/10 passing with 0 failures. No real OpenAI API key required — embeddings are mocked via `patch.object(ingest, "_get_vectorstore", ...)`. This satisfies the key CI/CD constraint.

### P6. Collection name `"crag_corpus"` hard-coded as module constant

`CHROMA_COLLECTION = "crag_corpus"` is set as a module-level constant used in `_get_vectorstore()`. Satisfies the constraint that the retriever in `graph/nodes.py` must find the same collection name.

### P7. Import deviations from plan properly documented

Three import-level deviations (langchain_core, langchain_text_splitters, test patching strategy) are all documented in the plan's Implementation Notes section. This is exactly the process the `pr-implement.md` instructions require.

---

## Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| T1: `from ingest import ingest_pdfs, IngestResult` succeeds without OPENAI_API_KEY | PASS |
| T1: `IngestResult` has exactly 3 fields: ingested, skipped, failed, all `list[str]` | PASS |
| T1: `ingest_pdfs` type sig `(file_paths: list[Path]) -> IngestResult` | PASS |
| T2: Re-ingesting same PDF returns filename in `skipped`, zero new chunks | PASS |
| T2: Different file with different bytes not classified as duplicate | PASS |
| T2: SHA256 from raw bytes not extracted text | PASS |
| T3: PDF with extractable text returns non-empty string | PASS |
| T3: Empty PDF raises ValueError with "No extractable text found" | PASS |
| T3: Corrupted file caught and added to `failed` | PASS |
| T3: Processing continues after single file failure | PASS |
| T4: Each chunk has `metadata["source"]`, `["doc_hash"]`, `["page"]` | PASS |
| T4: `page` metadata is int | PASS |
| T5: `CHROMA_PERSIST_DIR` env var read with default `./chroma_db` | PASS (code) |
| T5: Collection name `"crag_corpus"` used | PASS |
| T6: All 10 tests pass with `pytest tests/test_ingest.py -v` | PASS |
| T6: No OPENAI_API_KEY required | PASS |
| T6: Test isolation — no shared Chroma state | PASS |

---

## Architecture Constraints Checklist

| Constraint | Status |
|-----------|--------|
| No OCR dependency (no tesseract/pytesseract) | PASS |
| pypdf only for PDF parsing | PASS |
| SHA256 from raw bytes before chunking | PASS |
| `doc_hash` stored as metadata on every chunk | PASS |
| Batch error isolation — one failure does not abort batch | PASS |
| `CHROMA_PERSIST_DIR` from env var, default `./chroma_db` | PASS |
| `OPENAI_API_KEY` via python-dotenv `load_dotenv()` | PASS |
| `OpenAIEmbeddings` from `langchain_openai` (no raw openai SDK) | PASS |
| Collection name `"crag_corpus"` | PASS |
| Unit tests require no real OPENAI_API_KEY | PASS |

---

## Verdict

```
Verdict: NEEDS_WORK

Issues requiring attention before opening a PR:

I1 (Important): requirements.txt pins pypdf==4.* but installed/tested version is pypdf 6.x.
     Fix: Change `pypdf==4.*` to `pypdf>=6.0,<7` in requirements.txt.

I2 (Important): test_chroma_persist_dir_env_override does not actually test the env-var code path
     — it mocks _get_vectorstore entirely, so the CHROMA_PERSIST_DIR constraint is not verified.
     Fix: Rewrite to patch `ingest.CHROMA_PERSIST_DIR` and call the real _get_vectorstore().

I3 (Important): langchain-text-splitters is a direct dependency of ingest.py but absent from requirements.txt.
     Fix: Add `langchain-text-splitters` to requirements.txt.

After addressing I1–I3, re-run /pr-review to confirm PASS.
```

---

Review written: thoughts/shared/reviews/pdf-ingestion-review.md
