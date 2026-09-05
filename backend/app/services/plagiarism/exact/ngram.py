"""N-gram shingling and Jaccard similarity.

Adapted from Aegis Integrity (MIT).
Provides rapid word and character n-gram similarity scoring.
"""

from __future__ import annotations

import re


def get_word_ngrams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    """Extract word-level n-grams from text."""
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return round(intersection / union, 4) if union > 0 else 0.0


def ngram_overlap_score(text_a: str, text_b: str, n: int = 3) -> float:
    """Compute n-gram Jaccard overlap between two texts."""
    ngrams_a = get_word_ngrams(text_a, n)
    ngrams_b = get_word_ngrams(text_b, n)
    return jaccard_similarity(ngrams_a, ngrams_b)
