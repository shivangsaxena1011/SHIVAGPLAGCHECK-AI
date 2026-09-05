"""Text matching utilities for reference checking.

Adapted from RefChecker (MIT).
"""

from __future__ import annotations

import re
import unicodedata


def clean_title(title: str) -> str:
    """Normalize paper title for fuzzy comparison."""
    if not title:
        return ""
    # NFKC normalize
    text = unicodedata.normalize("NFKC", title)
    # Lowercase and remove punctuation
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(text.split())


def title_similarity(title_a: str, title_b: str) -> float:
    """Compute word-level Jaccard similarity between two paper titles."""
    clean_a = clean_title(title_a)
    clean_b = clean_title(title_b)

    words_a = set(clean_a.split())
    words_b = set(clean_b.split())

    if not words_a or not words_b:
        return 0.0

    intersection = words_a.intersection(words_b)
    union = words_a.union(words_b)
    return len(intersection) / len(union)


def author_match(claimed_authors: list[str], resolved_authors: list[str]) -> bool:
    """Check if at least one primary author surname matches."""
    if not claimed_authors or not resolved_authors:
        return True  # Cannot disprove

    claimed_surnames = {a.strip().split()[-1].lower() for a in claimed_authors if a.strip()}
    resolved_surnames = {a.strip().split()[-1].lower() for a in resolved_authors if a.strip()}

    return bool(claimed_surnames.intersection(resolved_surnames))
