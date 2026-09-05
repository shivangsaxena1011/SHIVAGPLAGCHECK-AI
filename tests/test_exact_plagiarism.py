"""Tests for Winnowing, Seed-Extend Alignment, and Interval Deduplication."""

import pytest
from app.services.plagiarism.exact.winnowing import fingerprint
from app.services.plagiarism.exact.alignment import align
from app.services.plagiarism.exact.intervals import (
    merge_intervals,
    subtract_intervals,
    calculate_coverage,
    total_interval_length,
)


def test_winnowing_fingerprint_determinism():
    text = "The quick brown fox jumps over the lazy dog."
    fp1 = fingerprint(text)
    fp2 = fingerprint(text)
    assert fp1 == fp2
    assert len(fp1) > 0
    # Different text produces different fingerprints
    fp_diff = fingerprint("A completely unrelated sentence discussing celestial mechanics.")
    assert set(fp1).intersection(set(fp_diff)) == set()


def test_seed_extend_exact_copy():
    with open("tests/fixtures/exact_original.txt", "r", encoding="utf-8") as f:
        orig = f.read()
    with open("tests/fixtures/exact_copy.txt", "r", encoding="utf-8") as f:
        copy = f.read()

    passages = align(copy, orig, min_seed_len=12, min_passage_len=15)
    assert len(passages) > 0

    # Passage score should be near 1.0
    top_p = passages[0]
    assert top_p.score >= 0.95
    assert top_p.match_type == "EXACT"
    # Extracted text should match
    assert copy[top_p.query_start : top_p.query_end].strip() in orig


def test_interval_merging_no_double_counting():
    # Overlapping intervals: [10, 30), [20, 50), [60, 80)
    raw = [(10, 30), (20, 50), (60, 80)]
    merged = merge_intervals(raw)
    assert merged == [(10, 50), (60, 80)]
    assert total_interval_length(merged) == 40 + 20 == 60


def test_interval_subtraction():
    base = [(0, 100)]
    # Quote from 20 to 40, Bibliography from 80 to 100
    remove = [(20, 40), (80, 100)]
    remaining = subtract_intervals(base, remove)
    assert remaining == [(0, 20), (40, 80)]
    assert total_interval_length(remaining) == 20 + 40 == 60
    assert calculate_coverage(remaining, 100) == 60.0
