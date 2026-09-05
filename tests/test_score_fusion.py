"""Tests for Deterministic Score Fusion and Coverage Math."""

import pytest
from app.schemas.evidence import MatchEvidenceSchema
from app.schemas.check import CheckOptions
from app.services.scoring.score_fusion import ScoreFusionEngine


def test_score_fusion_union_coverage():
    engine = ScoreFusionEngine()

    matches = [
        MatchEvidenceSchema(
            id="m1",
            submission_id="sub_1",
            source_id="src_A",
            detection_type="EXACT",
            confidence=1.0,
            similarity=1.0,
            submitted_text="This is an exact verbatim phrase copied directly from another author.",
            submission_start=100,
            submission_end=200,
        ),
        MatchEvidenceSchema(
            id="m2",
            submission_id="sub_1",
            source_id="src_B",
            detection_type="SEMANTIC",
            confidence=0.85,
            similarity=0.85,
            submitted_text="Overlapping conceptual passage spanning partly across the exact match.",
            submission_start=150,  # Overlaps [100, 200) by 50 chars!
            submission_end=250,
        ),
    ]

    total_chars = 1000
    total_words = 150

    options = CheckOptions(exclude_quotes=False, exclude_small_matches=False)
    result = engine.fuse(
        matches=matches,
        total_chars=total_chars,
        total_words=total_words,
        quote_spans=[],
        bib_spans=[],
        citation_spans=[],
        options=options,
    )

    # Union interval is [100, 250) = 150 chars total
    # 150 / 1000 = 15.0%
    assert result.breakdown.overall_similarity == 15.0
    # Must NOT be 10.0 + 10.0 = 20.0%
    assert result.breakdown.overall_similarity < 20.0
