"""Submission and Check Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.evidence import MatchEvidenceSchema, AIFindingSchema, CitationItemSchema, ReferenceItemSchema


class CheckOptions(BaseModel):
    scan_local_corpus: bool = True
    scan_external: bool = False
    run_ai_detection: bool = True
    verify_citations: bool = True
    exclude_quotes: bool = True
    exclude_bibliography: bool = True
    exclude_small_matches: bool = True
    exclude_citations: bool = True


class CheckStatusResponse(BaseModel):
    id: str
    status: str
    progress: int
    current_stage: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SourceContribution(BaseModel):
    source_id: str
    title: str
    authors: str | None = None
    publication: str | None = None
    year: str | None = None
    url: str | None = None
    doi: str | None = None
    source_type: str
    similarity_contribution: float
    matched_words: int
    primary_match_type: str
    color_index: int = 0


class SimilarityBreakdown(BaseModel):
    overall_similarity: float
    exact_similarity: float
    near_exact_similarity: float
    semantic_similarity: float
    self_plagiarism_similarity: float = 0.0
    matched_word_count: int
    total_words: int
    excluded_quote_words: int = 0
    excluded_bibliography_words: int = 0


class AISummary(BaseModel):
    overall_likelihood: float  # e.g. 52.0%
    confidence_band: str  # "Moderate-High Confidence", "Preliminary Signal"
    high_signal_sections: int
    medium_signal_sections: int
    total_sentences: int
    detector_version: str = "Aegis-Ensemble-v2.6"
    methodology_notes: str = "Ensemble: Perplexity, burstiness, stylometric tells, and ESL calibration."


class CitationSummary(BaseModel):
    total_references: int
    verified_count: int
    mismatch_count: int
    hallucinated_count: int
    unresolvable_count: int
    in_text_citations_count: int


class DocumentPageSchema(BaseModel):
    page_number: int
    char_start: int
    char_end: int
    text: str


class CheckResultResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    file_type: str
    word_count: int
    char_count: int
    page_count: int
    created_at: datetime
    scores: SimilarityBreakdown
    sources: list[SourceContribution]
    ai_summary: AISummary
    citation_summary: CitationSummary
    options: CheckOptions
    pages: list[DocumentPageSchema]
    matches: list[MatchEvidenceSchema]
    ai_findings: list[AIFindingSchema]
    citations: list[CitationItemSchema]
    references: list[ReferenceItemSchema]
