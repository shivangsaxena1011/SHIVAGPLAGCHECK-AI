"""Tests for AI writing likelihood estimation and ESL calibration."""

import pytest
from app.services.ai_detection.ai_detector import AIContentDetector
from app.services.document.extractor import DocumentExtractor


def test_ai_vs_human_text_separation():
    detector = AIContentDetector()
    extractor = DocumentExtractor()

    with open("tests/fixtures/ai_like_text.txt", "r", encoding="utf-8") as f:
        ai_text = f.read().strip()
    with open("tests/fixtures/human_like_text.txt", "r", encoding="utf-8") as f:
        human_text = f.read().strip()

    ai_doc = extractor.extract(ai_text.encode("utf-8"), "txt")
    human_doc = extractor.extract(human_text.encode("utf-8"), "txt")

    ai_sentences = [
        {"sentence_index": s.sentence_index, "char_start": s.char_start, "char_end": s.char_end, "page_number": 1, "text": s.text}
        for s in ai_doc.sentences
    ]
    human_sentences = [
        {"sentence_index": s.sentence_index, "char_start": s.char_start, "char_end": s.char_end, "page_number": 1, "text": s.text}
        for s in human_doc.sentences
    ]

    ai_result = detector.analyze_document(ai_text, ai_sentences)
    human_result = detector.analyze_document(human_text, human_sentences)

    # The AI text containing "delve into", "a testament to", "tapestry of" must yield a higher score
    assert ai_result.overall_likelihood > human_result.overall_likelihood
    assert ai_result.high_signal_count > 0
    assert "LLM" in ai_result.sentence_signals[0].primary_signal or "transition" in ai_result.sentence_signals[0].primary_signal.lower()
