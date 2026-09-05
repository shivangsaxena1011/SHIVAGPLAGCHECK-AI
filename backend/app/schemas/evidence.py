"""Universal Match Evidence and Findings Schemas.

Complies strictly with Section 12 Universal Match Evidence Schema.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


DetectionType = Literal[
    "EXACT",
    "NEAR_EXACT",
    "SEMANTIC",
    "NGRAM",
    "SELF_PLAGIARISM",
    "QUOTE",
    "CITATION",
    "BOILERPLATE",
    "AI_SIGNAL",
    "REFERENCE_ISSUE",
]


class MatchEvidenceSchema(BaseModel):
    """Universal evidence object standard across all detectors and reports."""

    id: str
    submission_id: str
    source_id: str | None = None
    source_type: str = "LOCAL_CORPUS"
    detection_type: DetectionType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Algorithmic confidence score")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score between passage pair")
    source_similarity_contribution: float = Field(
        0.0, description="Percentage contribution of this source to overall similarity"
    )
    submitted_text: str
    source_text: str | None = None
    submission_page: int = 1
    source_page: int | None = 1
    submission_start: int = Field(..., description="Character offset start in submission")
    submission_end: int = Field(..., description="Character offset end in submission")
    source_start: int | None = 0
    source_end: int | None = 0
    sentence_index: int = 0
    paragraph_index: int = 0
    evidence_reason: str | None = None
    url: str | None = None
    doi: str | None = None
    title: str | None = None
    authors: str | None = None


class AIFindingSchema(BaseModel):
    """Sentence-level AI writing indicator."""

    id: str
    sentence_index: int
    sentence_text: str
    char_start: int
    char_end: int
    page_number: int
    likelihood_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    primary_signal: str
    details: dict[str, float | str] | None = None


class CitationItemSchema(BaseModel):
    id: str
    raw_text: str
    cite_key: str | None = None
    page_number: int = 1
    char_start: int
    char_end: int
    claimed_authors: str | None = None
    claimed_year: str | None = None
    claimed_title: str | None = None
    doi: str | None = None


class ReferenceItemSchema(BaseModel):
    id: str
    raw_text: str
    parsed_title: str | None = None
    parsed_authors: str | None = None
    parsed_year: str | None = None
    doi: str | None = None
    verification_status: Literal["VALID", "MISMATCH", "HALLUCINATED", "NOT_FOUND", "UNRESOLVABLE", "UNVERIFIED"]
    confidence: float = 1.0
    issues: list[str] = []
