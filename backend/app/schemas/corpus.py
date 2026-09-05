"""Corpus Management Schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CorpusDocumentCreate(BaseModel):
    title: str
    authors: str | None = None
    publication: str | None = None
    year: str | None = None
    url: str | None = None
    doi: str | None = None
    text: str


class CorpusDocumentResponse(BaseModel):
    id: str
    title: str
    authors: str | None = None
    publication: str | None = None
    year: str | None = None
    url: str | None = None
    doi: str | None = None
    source_type: str
    checksum: str
    word_count: int
    chunks_count: int
    created_at: datetime


class CorpusStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_fingerprints: int
