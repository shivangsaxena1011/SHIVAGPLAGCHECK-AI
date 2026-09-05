"""Tests for SBERT semantic similarity and paraphrase detection."""

import pytest
from app.services.plagiarism.semantic.semantic import SemanticDetector


def test_semantic_paraphrase_detection():
    detector = SemanticDetector(cosine_threshold=0.65)

    with open("tests/fixtures/paraphrased_original.txt", "r", encoding="utf-8") as f:
        orig_text = f.read().strip()
    with open("tests/fixtures/paraphrased_copy.txt", "r", encoding="utf-8") as f:
        copy_text = f.read().strip()

    query_sentences = [{
        "sentence_index": 0,
        "char_start": 0,
        "char_end": len(copy_text),
        "page_number": 1,
        "text": copy_text,
    }]

    matches = detector.find_matches(
        query_sentences=query_sentences,
        source_id="src_1",
        source_title="Autonomous Driving Research",
        candidate_sentences=[orig_text, "A totally unrelated recipe for blueberry muffins."],
    )

    assert len(matches) == 1
    top_match = matches[0]
    assert top_match.cosine_score >= 0.65
    assert top_match.is_paraphrase is True
    assert top_match.source_sentence == orig_text
