"""Corpus Index Manager.

Maintains in-memory inverted indices of fingerprints and source documents,
enabling fast retrieval of candidates before seed-and-extend alignment.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.services.corpus.ingestion import CorpusIngestionService, IndexedSourceDocument


@dataclass
class CandidateMatch:
    source_id: str
    chunk_index: int
    shared_fingerprints_count: int


class CorpusIndexManager:
    """Manages the in-memory inverted fingerprint index for rapid L1 retrieval."""

    def __init__(self):
        self.ingestion_service = CorpusIngestionService()
        self.sources: dict[str, IndexedSourceDocument] = {}
        # Inverted index: fingerprint_hash -> list of (source_id, chunk_index)
        self.inverted_index: dict[int, list[tuple[str, int]]] = defaultdict(list)

    def add_document(
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
        """Process and index a source document."""
        doc = self.ingestion_service.process_document(
            source_id=source_id,
            title=title,
            text=text,
            authors=authors,
            publication=publication,
            year=year,
            url=url,
            doi=doi,
        )

        self.sources[source_id] = doc

        # Update inverted index
        for chunk_idx, fps in doc.fingerprints_by_chunk.items():
            for fp in fps:
                self.inverted_index[fp].append((source_id, chunk_idx))

        return doc

    def query_fingerprints(
        self,
        query_fingerprints: list[int],
        min_overlap: int = 2,
    ) -> list[CandidateMatch]:
        """Query inverted index with query fingerprints and rank candidates by shared count."""
        if not query_fingerprints:
            return []

        counts: dict[tuple[str, int], int] = defaultdict(int)

        for fp in query_fingerprints:
            if fp in self.inverted_index:
                for target in self.inverted_index[fp]:
                    counts[target] += 1

        candidates: list[CandidateMatch] = []
        for (src_id, chunk_idx), hit_count in counts.items():
            if hit_count >= min_overlap:
                candidates.append(
                    CandidateMatch(
                        source_id=src_id,
                        chunk_index=chunk_idx,
                        shared_fingerprints_count=hit_count,
                    )
                )

        return sorted(candidates, key=lambda c: -c.shared_fingerprints_count)

    def get_source(self, source_id: str) -> IndexedSourceDocument | None:
        """Get an indexed source document by ID."""
        return self.sources.get(source_id)

    async def load_from_db(self, session: Any) -> int:
        """Hydrate in-memory inverted index from database Source records."""
        from sqlalchemy import select
        from app.models.entities import Source
        stmt = select(Source)
        res = await session.execute(stmt)
        sources = res.scalars().all()
        for s in sources:
            if s.id not in self.sources:
                self.add_document(
                    source_id=s.id,
                    title=s.title,
                    text=s.text,
                    authors=s.authors,
                    publication=s.publication,
                    year=s.year,
                    url=s.url,
                    doi=s.doi,
                )
        return len(self.sources)

    def total_documents(self) -> int:
        return len(self.sources)

    def total_chunks(self) -> int:
        return sum(len(doc.chunks) for doc in self.sources.values())

    def total_fingerprints(self) -> int:
        return len(self.inverted_index)


# Global singleton instance for application lifespan
corpus_manager = CorpusIndexManager()
