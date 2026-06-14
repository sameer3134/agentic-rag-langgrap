"""Unit tests for ingest.py.

Run with: pytest tests/test_ingest.py -v
No OPENAI_API_KEY required — embeddings are mocked.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# PDF builder helper — produces a PDF pypdf 6.x can parse
# ---------------------------------------------------------------------------

def _build_pdf(text: str) -> bytes:
    """Create a minimal valid PDF with extractable text using correct xref offsets."""
    parts: list[bytes] = []
    offsets: list[int] = []

    header = b"%PDF-1.4\n"
    parts.append(header)

    def _add_obj(obj_bytes: bytes) -> None:
        offsets.append(sum(len(p) for p in parts))
        parts.append(obj_bytes)

    _add_obj(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    _add_obj(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    _add_obj(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj\n"
    )
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET".encode()
    _add_obj(
        b"4 0 obj\n<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream + b"\nendstream\nendobj\n"
    )
    _add_obj(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    xref_pos = sum(len(p) for p in parts)
    xref = b"xref\n0 6\n"
    xref += b"0000000000 65535 f \r\n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \r\n".encode()

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    return b"".join(parts) + xref + trailer


def _build_empty_pdf() -> bytes:
    """Create a minimal PDF whose page has no text (empty content stream)."""
    parts: list[bytes] = []
    offsets: list[int] = []

    header = b"%PDF-1.4\n"
    parts.append(header)

    def _add_obj(obj_bytes: bytes) -> None:
        offsets.append(sum(len(p) for p in parts))
        parts.append(obj_bytes)

    _add_obj(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    _add_obj(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    _add_obj(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R >>\n"
        b"endobj\n"
    )
    _add_obj(b"4 0 obj\n<< /Length 0 >>\nstream\n\nendstream\nendobj\n")

    xref_pos = sum(len(p) for p in parts)
    xref = b"xref\n0 5\n"
    xref += b"0000000000 65535 f \r\n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \r\n".encode()

    trailer = (
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode()
        + b"\n%%EOF\n"
    )
    return b"".join(parts) + xref + trailer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """Isolated Chroma persist directory per test."""
    return str(tmp_path / "chroma_test")


@pytest.fixture
def fake_embeddings():
    """Mock embedding object that satisfies Chroma's embedding_function interface."""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.0] * 1536]
    mock.embed_query.return_value = [0.0] * 1536
    return mock


@pytest.fixture
def simple_pdf(tmp_path) -> Path:
    """Create a minimal valid PDF with extractable text."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(_build_pdf("Hello World this is a test document with extractable content."))
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path) -> Path:
    """A PDF with no extractable text."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(_build_empty_pdf())
    return pdf_path


def _make_mock_vectorstore(persist_dir: str, fake_embeddings) -> "Chroma":
    """Return a real Chroma collection backed by PersistentClient but with mocked embeddings."""
    from langchain_community.vectorstores import Chroma
    return Chroma(
        collection_name="crag_corpus",
        embedding_function=fake_embeddings,
        persist_directory=persist_dir,
    )


# ---------------------------------------------------------------------------
# Dedup tests
# ---------------------------------------------------------------------------

class TestDedup:
    def test_reingest_same_file_returns_skipped(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Re-ingesting the same PDF bytes must return skipped, add zero chunks."""
        import ingest

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result1 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result1.ingested, f"Expected ingested, got: {result1}"

            result2 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result2.skipped, f"Expected skipped, got: {result2}"
            assert simple_pdf.name not in result2.ingested

    def test_dedup_is_byte_based_not_filename_based(self, tmp_chroma_dir, fake_embeddings, simple_pdf, tmp_path):
        """A copy of the same bytes under a different name is still a duplicate."""
        copy_path = tmp_path / "copy_of_test.pdf"
        copy_path.write_bytes(simple_pdf.read_bytes())
        import ingest

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result1 = ingest_pdfs([simple_pdf])
            assert simple_pdf.name in result1.ingested, f"Expected ingested, got: {result1}"

            result2 = ingest_pdfs([copy_path])
            assert copy_path.name in result2.skipped, f"Expected skipped for byte-copy, got: {result2}"

    def test_reingest_adds_zero_new_chunks(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Chunk count in Chroma must not change after dedup skip."""
        import chromadb
        import ingest

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            ingest_pdfs([simple_pdf])

            client = chromadb.PersistentClient(path=tmp_chroma_dir)
            collection = client.get_collection("crag_corpus")
            count_after_first = collection.count()

            ingest_pdfs([simple_pdf])
            count_after_second = collection.count()

        assert count_after_first == count_after_second, (
            f"Chunk count changed after re-ingest: {count_after_first} -> {count_after_second}"
        )


# ---------------------------------------------------------------------------
# Chunking tests
# ---------------------------------------------------------------------------

class TestChunking:
    def test_chunk_count_in_expected_range(self):
        """A ~3000-char text should produce 2–6 chunks with size=1000, overlap=200."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        long_text = "A" * 3000
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_text(long_text)
        assert 2 <= len(chunks) <= 6, f"Expected 2–6 chunks, got {len(chunks)}"

    def test_chunk_metadata_fields(self, simple_pdf):
        """Each chunk must have source, doc_hash, and page metadata fields."""
        import ingest as ing
        sha256_hex = hashlib.sha256(simple_pdf.read_bytes()).hexdigest()
        docs = ing._chunk_pdf(simple_pdf, sha256_hex)
        assert len(docs) > 0, "Expected at least one chunk"
        for doc in docs:
            assert "source" in doc.metadata, "missing source"
            assert "doc_hash" in doc.metadata, "missing doc_hash"
            assert "page" in doc.metadata, "missing page"
            assert doc.metadata["source"] == simple_pdf.name
            assert doc.metadata["doc_hash"] == sha256_hex
            assert isinstance(doc.metadata["page"], int)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_empty_pdf_returns_failed(self, tmp_chroma_dir, fake_embeddings, empty_pdf):
        """A PDF with no extractable text must appear in failed with a non-empty reason."""
        import ingest

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result = ingest_pdfs([empty_pdf])
        assert len(result.failed) == 1, f"Expected 1 failed, got: {result}"
        assert empty_pdf.name in result.failed[0]
        reason = result.failed[0].split(": ", 1)[1]
        assert reason.strip() != "", "reason must not be empty"

    def test_corrupt_file_returns_failed(self, tmp_chroma_dir, fake_embeddings, tmp_path):
        """A corrupt file (not valid PDF) must appear in failed, not raise."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_bytes(b"this is not a pdf")
        import ingest

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result = ingest_pdfs([corrupt])
        assert len(result.failed) == 1, f"Expected 1 failed, got: {result}"
        assert "corrupt.pdf" in result.failed[0]

    def test_batch_continues_after_failure(self, tmp_chroma_dir, fake_embeddings, simple_pdf, empty_pdf, tmp_path):
        """[valid, empty, valid] batch returns 2 ingested and 1 failed."""
        import ingest as ing
        from langchain_core.documents import Document

        # Create a second valid PDF with different bytes
        simple_pdf2 = tmp_path / "second_valid.pdf"
        simple_pdf2.write_bytes(_build_pdf("Second document with completely different content here."))

        def mock_load(fp):
            if fp.name == empty_pdf.name:
                raise ValueError("No extractable text found")
            return "Some valid text content " * 50

        def mock_chunk(fp, sha256):
            return [Document(
                page_content="chunk text",
                metadata={"source": fp.name, "doc_hash": sha256, "page": 0}
            )]

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ing, "_get_vectorstore", side_effect=mock_get_vs), \
             patch.object(ing, "_load_pdf_text", side_effect=mock_load), \
             patch.object(ing, "_chunk_pdf", side_effect=mock_chunk):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf, empty_pdf, simple_pdf2])

        assert len(result.ingested) == 2, f"Expected 2 ingested, got: {result}"
        assert len(result.failed) == 1, f"Expected 1 failed, got: {result}"
        assert empty_pdf.name in result.failed[0]


# ---------------------------------------------------------------------------
# Hash metadata test
# ---------------------------------------------------------------------------

class TestHashMetadata:
    def test_doc_hash_matches_sha256_of_source_bytes(self, tmp_chroma_dir, fake_embeddings, simple_pdf):
        """Every ingested chunk's doc_hash must equal SHA256 of source file bytes."""
        import chromadb
        import ingest
        expected_hash = hashlib.sha256(simple_pdf.read_bytes()).hexdigest()

        def mock_get_vs():
            return _make_mock_vectorstore(tmp_chroma_dir, fake_embeddings)

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf])
        assert simple_pdf.name in result.ingested, f"Expected ingested, got: {result}"

        client = chromadb.PersistentClient(path=tmp_chroma_dir)
        collection = client.get_collection("crag_corpus")
        items = collection.get(include=["metadatas"])
        for meta in items["metadatas"]:
            assert meta["doc_hash"] == expected_hash, (
                f"doc_hash mismatch: {meta['doc_hash']} != {expected_hash}"
            )


# ---------------------------------------------------------------------------
# Environment variable test
# ---------------------------------------------------------------------------

class TestEnvConfig:
    def test_chroma_persist_dir_env_override(self, tmp_path, fake_embeddings, simple_pdf):
        """CHROMA_PERSIST_DIR env var must override the default ./chroma_db path."""
        custom_dir = str(tmp_path / "custom_chroma")
        import ingest

        def mock_get_vs():
            # Create vectorstore in the custom directory
            from langchain_community.vectorstores import Chroma
            return Chroma(
                collection_name="crag_corpus",
                embedding_function=fake_embeddings,
                persist_directory=custom_dir,
            )

        with patch.object(ingest, "_get_vectorstore", side_effect=mock_get_vs):
            from ingest import ingest_pdfs
            result = ingest_pdfs([simple_pdf])
        assert simple_pdf.name in result.ingested, f"Expected ingested, got: {result}"
        assert os.path.exists(custom_dir), "Custom CHROMA_PERSIST_DIR was not created"
