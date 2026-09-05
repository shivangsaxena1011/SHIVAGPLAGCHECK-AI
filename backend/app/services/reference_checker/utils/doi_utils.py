"""DOI extraction and normalization utilities.

Adapted from RefChecker (MIT).
"""

from __future__ import annotations

import re


def extract_doi_from_url(url: str) -> str | None:
    """Extract DOI from a URL."""
    if not url:
        return None

    if "doi.org" not in url and "doi:" not in url:
        return None

    doi_patterns = [
        r"doi\.org/([^/\s\?#]+(?:/[^/\s\?#]+)*)",
        r"doi:([^/\s\?#]+(?:/[^/\s\?#]+)*)",
    ]

    for pattern in doi_patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            doi_candidate = match.group(1).rstrip(".")
            if doi_candidate.startswith("10.") and "/" in doi_candidate and len(doi_candidate) > 6:
                return doi_candidate

    return None


def extract_doi(text: str) -> str | None:
    """Extract DOI directly from freeform text or citation."""
    if not text:
        return None

    # First check URLs
    url_doi = extract_doi_from_url(text)
    if url_doi:
        return normalize_doi(url_doi)

    # Standard DOI pattern: 10.NNNN/...
    match = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b", text)
    if match:
        raw = match.group(1).rstrip(".,;)")
        return normalize_doi(raw)

    return None


def normalize_doi(doi: str) -> str:
    """Normalize DOI by stripping prefixes and converting to lowercase."""
    if not doi:
        return ""
    clean = doi.strip()
    clean = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^doi:\s*", "", clean, flags=re.IGNORECASE)
    return clean.lower()
