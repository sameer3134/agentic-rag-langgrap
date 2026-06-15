"""PDF ingestion — chunks, embeds, and stores PDFs in a per-user Chroma collection."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

import pypdf
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()


@dataclass
class IngestResult:
    ingested: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)


def _get_vectorstore(collection_name: str) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
    )


def ingest_pdfs(file_paths: list[Path], collection_name: str) -> IngestResult:
    vectorstore = _get_vectorstore(collection_name)

    existing = vectorstore.get(include=["metadatas"])
    existing_hashes = {
        m["doc_hash"]
        for m in existing["metadatas"]
        if m and "doc_hash" in m
    }

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    result = IngestResult()

    for path in file_paths:
        doc_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if doc_hash in existing_hashes:
            result.skipped.append(path)
            continue

        try:
            reader = pypdf.PdfReader(str(path))
            texts, metas = [], []
            for page_num, page in enumerate(reader.pages):
                for chunk in splitter.split_text(page.extract_text() or ""):
                    if chunk.strip():
                        texts.append(chunk)
                        metas.append({"source": path.name, "doc_hash": doc_hash, "page": page_num})

            if not texts:
                result.failed.append((path, "No extractable text found"))
                continue

            vectorstore.add_texts(texts, metadatas=metas)
            result.ingested.append(path)
        except Exception as exc:
            result.failed.append((path, str(exc)))

    return result
