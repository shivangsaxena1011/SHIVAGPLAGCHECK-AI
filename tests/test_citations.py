"""Tests for Citation Parsing, DOI normalization, and Reference Verification."""

import pytest
from app.services.citations.citation_detector import CitationDetector
from app.services.reference_checker.utils.doi_utils import extract_doi, normalize_doi


def test_doi_extraction():
    doi_raw = "https://doi.org/10.1145/3372278.3390678"
    assert extract_doi(doi_raw) == "10.1145/3372278.3390678"

    text_with_doi = "Paper published in Nature 2021. doi:10.1038/s41586-021-03819-2."
    assert extract_doi(text_with_doi) == "10.1038/s41586-021-03819-2"


def test_citation_detector_in_text_and_references():
    detector = CitationDetector(offline=True)

    with open("tests/fixtures/citation_sample.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Fake page span
    from app.services.document.extractor import PageSpan
    pages = [PageSpan(page_number=1, char_start=0, char_end=len(text), text=text)]

    in_text = detector.find_in_text_citations(text, pages)
    assert len(in_text) >= 2  # [1] and (Brown et al., 2020)

    refs = detector.extract_and_verify_references(text)
    assert len(refs) >= 2
    assert refs[0].doi == "10.48550/arxiv.1706.03762"
