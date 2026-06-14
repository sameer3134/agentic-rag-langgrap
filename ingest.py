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

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "crag_corpus"


@dataclass
class IngestResult:
    """Structured result returned by ingest_pdfs."""

    ingested: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def _compute_sha256(file_path: Path) -> str:
    """Return hex SHA256 digest of raw file bytes."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _is_already_ingested(vectorstore: Chroma, sha256_hex: str) -> bool:
    """Return True if any chunk with doc_hash==sha256_hex exists in the collection."""
    try:
        results = vectorstore.get(where={"doc_hash": sha256_hex}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        # Empty collection raises in some Chroma 0.5.x builds
        return False


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


def _get_vectorstore() -> Chroma:
    """Return (or create) the persistent Chroma vector store."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


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
