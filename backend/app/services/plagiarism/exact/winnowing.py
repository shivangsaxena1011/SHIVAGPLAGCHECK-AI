"""Winnowing fingerprints for exact and near-exact plagiarism retrieval.

Adapted from Noplag Engine (Apache-2.0), implementing robust winnowing from
Schleimer, Wilkerson & Aiken (SIGMOD 2003) — "Winnowing: Local Algorithms
for Document Fingerprinting".
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

# Citation/editorial markers stripped during fingerprinting
_CITATION_MARKER_RE = re.compile(
    r"\[\s*(?:"
    r"\d{1,4}"  # [1] [12] [1234]
    r"|citation needed|clarification needed|verification needed|page needed"
    r"|note\s*\d*|nb\s*\d*|dead link|sic|update|edit"
    r"|by whom|according to whom|when|who|why|where"
    r")\??\s*\]",
    re.IGNORECASE,
)


def fingerprint(text: str, k: int = 5, w: int = 8) -> list[int]:
    """Compute the winnowing fingerprint of `text`.

    Returns a sorted, deduplicated list of signed 64-bit ints, each
    derived from a k-gram of the normalized input.
    """
    normalized = normalize_for_fingerprint(text)
    if len(normalized) < k:
        return []

    hashes = [_hash_kgram(normalized[i : i + k]) for i in range(len(normalized) - k + 1)]
    selected = _winnow(hashes, w)
    return sorted(selected)


def normalize_for_fingerprint(text: str) -> str:
    """NFKC normalization, lowercase, strip bracketed markers, collapse whitespace."""
    nfkc = unicodedata.normalize("NFKC", text)
    de_cited = _CITATION_MARKER_RE.sub("", nfkc)
    return " ".join(de_cited.lower().split())


def _hash_kgram(s: str) -> int:
    """Hash a k-gram into a 64-bit signed integer using Blake2b."""
    digest = hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=True)


def _winnow(hashes: list[int], w: int) -> set[int]:
    """Select the rightmost minimum from sliding windows of size w."""
    if not hashes:
        return set()
    if len(hashes) <= w:
        return {min(hashes)}

    selected_positions: set[int] = set()
    last_emitted = -1
    for window_start in range(len(hashes) - w + 1):
        min_pos = window_start
        for j in range(window_start + 1, window_start + w):
            if hashes[j] <= hashes[min_pos]:
                min_pos = j
        if min_pos != last_emitted:
            selected_positions.add(min_pos)
            last_emitted = min_pos

    return {hashes[i] for i in selected_positions}
