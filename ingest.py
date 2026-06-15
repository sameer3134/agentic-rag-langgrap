"""PDF ingestion pipeline with per-user Chroma collection isolation.

Public API:
    ingest_pdfs(file_paths: list[Path], collection_name: str) -> IngestResult
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")


@dataclass
class IngestResult:
    ingested: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def _compute_sha256(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _is_already_ingested(vectorstore: Chroma, sha256_hex: str) -> bool:
    try:
        results = vectorstore.get(where={"doc_hash": sha256_hex}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        return False


def _chunk_pdf(file_path: Path, sha256_hex: str) -> list[Document]:
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
            metadatas=[{"source": file_path.name, "doc_hash": sha256_hex, "page": page_num}],
        )
        all_docs.extend(chunks)
    return all_docs


def _get_vectorstore(collection_name: str) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=CHROMA_PERSIST_DIR,
    )


def ingest_pdfs(file_paths: list[Path], collection_name: str) -> IngestResult:
    """Chunk, embed, and store PDFs into the given user-scoped Chroma collection."""
    result = IngestResult()
    vectorstore = _get_vectorstore(collection_name)

    for file_path in file_paths:
        file_path = Path(file_path)
        try:
            sha256_hex = _compute_sha256(file_path)

            if _is_already_ingested(vectorstore, sha256_hex):
                result.skipped.append(file_path.name)
                continue

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
