"""Corpus Ingestion Service.

Processes and indexes source documents for plagiarism detection:
- Computes SHA-256 checksum for duplicate prevention.
- Splits into overlapping sentence chunks.
- Computes Winnowing fingerprints for each chunk.
- Builds in-memory and database inverted index.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from app.services.document.extractor import DocumentExtractor, SentenceSpan
from app.services.plagiarism.exact.chunking.sliding import chunk_sentences, DocumentChunk
from app.services.plagiarism.exact.winnowing import fingerprint


@dataclass
class IndexedSourceDocument:
    source_id: str
    title: str
    authors: str | None
    publication: str | None
    year: str | None
    url: str | None
    doi: str | None
    checksum: str
    word_count: int
    text: str
    chunks: list[DocumentChunk]
    fingerprints_by_chunk: dict[int, list[int]]  # chunk_index -> list[hash]


class CorpusIngestionService:
    """Service to ingest, validate, and index reference documents."""

    def __init__(self):
        self.extractor = DocumentExtractor()

    def process_document(
        self,
        source_id: str,
        title: str,
        text: str,
        authors: str | None = None,
        publication: str | None = None,
        year: str | None = None,
        url: str | None = None,
        doi: str | None = None,
    ) -> IndexedSourceDocument:
        """Process a source text and return indexed chunks with fingerprints."""
        # 1. Compute checksum
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # 2. Extract structured sentences
        doc = self.extractor.extract(text.encode("utf-8"), "txt", filename=title)
        
        # 3. Sliding chunking
        chunks = chunk_sentences(doc.sentences, window_size=4, step_size=2)
        if not chunks and text.strip():
            # Fallback single chunk
            chunks = [
                DocumentChunk(
                    chunk_index=0,
                    char_start=0,
                    char_end=len(text),
                    page_number=1,
                    text=text,
                    sentences=[],
                )
            ]

        # 4. Fingerprint each chunk
        fingerprints_by_chunk: dict[int, list[int]] = {}
        for chunk in chunks:
            fps = fingerprint(chunk.text)
            fingerprints_by_chunk[chunk.chunk_index] = fps

        return IndexedSourceDocument(
            source_id=source_id,
            title=title,
            authors=authors,
            publication=publication,
            year=year,
            url=url,
            doi=doi,
            checksum=checksum,
            word_count=doc.word_count,
            text=text,
            chunks=chunks,
            fingerprints_by_chunk=fingerprints_by_chunk,
        )
