"""Citation and Reference Integrity Detector.

Adapted from Aegis Integrity (MIT) and RefChecker (MIT).
Detects:
- In-text citations (IEEE [1], APA (Smith, 2020), Vancouver)
- Reference section parsing
- Online DOI resolution via Crossref REST API (polite pool)
- Hallucinated reference detection (e.g. LLM-invented citations or mismatched DOIs)
- Full offline fallback mode.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
import requests

from app.services.reference_checker.utils.doi_utils import extract_doi
from app.services.reference_checker.utils.text_utils import title_similarity, author_match

logger = logging.getLogger(__name__)


@dataclass
class InTextCitation:
    raw_text: str
    cite_key: str
    char_start: int
    char_end: int
    page_number: int


@dataclass
class ReferenceEntry:
    raw_text: str
    parsed_title: str | None
    parsed_authors: list[str] = field(default_factory=list)
    parsed_year: str | None = None
    doi: str | None = None
    verification_status: str = "UNVERIFIED"  # VALID, MISMATCH, HALLUCINATED, NOT_FOUND, UNRESOLVABLE
    confidence: float = 1.0
    issues: list[str] = field(default_factory=list)


class CitationDetector:
    """Extracts in-text citations and verifies reference entries."""

    # In-text IEEE: [1], [1, 2], [1-4]
    IEEE_CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+|\s*-\s*\d+)*)\]")
    
    # In-text APA: (Smith, 2020), (Smith & Jones, 2018), (Smith et al., 2021)
    APA_CITATION_RE = re.compile(
        r"\(([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?(?:\s*(?:&|and)\s*[A-Z][a-zA-Z]+)?),\s*([12]\d{3}[a-z]?)\)"
    )

    # Reference entry lines starting with [1] or 1. or Author (Year)
    REF_ENTRY_RE = re.compile(
        r"^(?:\[\d+\]|\d+\.|\b[A-Z][a-zA-Z]+,\s+[A-Z]\.).*$",
        re.MULTILINE,
    )

    CROSSREF_API = "https://api.crossref.org/works/"

    def __init__(self, email: str = "researcher@example.edu", offline: bool = False):
        self.email = email
        self.offline = offline
        self.headers = {"User-Agent": f"SHIVANG-PLAGCHECK-AI/1.0 (mailto:{self.email})"}

    def find_in_text_citations(self, full_text: str, pages: list) -> list[InTextCitation]:
        """Find in-text citation markers and calculate page numbers."""
        citations: list[InTextCitation] = []

        # Find IEEE markers
        for m in self.IEEE_CITATION_RE.finditer(full_text):
            c_start = m.start()
            c_end = m.end()
            page_num = self._find_page(c_start, pages)
            citations.append(
                InTextCitation(
                    raw_text=m.group(0),
                    cite_key=m.group(1),
                    char_start=c_start,
                    char_end=c_end,
                    page_number=page_num,
                )
            )

        # Find APA markers
        for m in self.APA_CITATION_RE.finditer(full_text):
            c_start = m.start()
            c_end = m.end()
            page_num = self._find_page(c_start, pages)
            citations.append(
                InTextCitation(
                    raw_text=m.group(0),
                    cite_key=f"{m.group(1)} {m.group(2)}",
                    char_start=c_start,
                    char_end=c_end,
                    page_number=page_num,
                )
            )

        return sorted(citations, key=lambda x: x.char_start)

    def extract_and_verify_references(
        self,
        full_text: str,
        bib_section_start: int | None = None,
    ) -> list[ReferenceEntry]:
        """Extract references from bibliography and verify against Crossref."""
        if bib_section_start is not None and bib_section_start < len(full_text):
            bib_text = full_text[bib_section_start:]
        else:
            # Search for standard section header
            match = re.search(r"\n(?:references|bibliography|works\s+cited)\s*\n", full_text, re.I)
            bib_text = full_text[match.end():] if match else ""

        if not bib_text.strip():
            return []

        # Split into individual reference lines
        lines = [line.strip() for line in bib_text.splitlines() if len(line.strip()) > 20]
        entries: list[ReferenceEntry] = []

        for line in lines:
            entry = self._parse_reference_entry(line)
            if not self.offline and entry.doi:
                self._verify_crossref(entry)
            entries.append(entry)

        return entries

    def _parse_reference_entry(self, line: str) -> ReferenceEntry:
        """Parse author, year, title, and DOI from a single reference string."""
        doi = extract_doi(line)

        # Year extraction: (2020) or 2020.
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
        parsed_year = year_match.group(1) if year_match else None

        # Title heuristic: text between quotes or after year
        title = None
        quote_title = re.search(r'["“]([^"”]{10,200})["”]', line)
        if quote_title:
            title = quote_title.group(1)
        else:
            # Guess segment between year and journal/doi
            parts = line.split(".")
            if len(parts) >= 3:
                title = parts[1].strip()
            elif len(parts) == 2:
                title = parts[0].strip()

        # Authors heuristic
        authors: list[str] = []
        author_part = line.split("(")[0] if "(" in line else line.split(".")[0]
        for author_str in re.split(r",\s*(?:and\s+)?|;\s*", author_part):
            clean_a = author_str.strip()
            if clean_a and len(clean_a) < 40 and not re.search(r"\d", clean_a):
                authors.append(clean_a)

        return ReferenceEntry(
            raw_text=line,
            parsed_title=title,
            parsed_authors=authors,
            parsed_year=parsed_year,
            doi=doi,
            verification_status="VALID" if doi else "UNVERIFIED",
            confidence=1.0,
            issues=[],
        )

    def _verify_crossref(self, entry: ReferenceEntry) -> None:
        """Query Crossref REST API to verify claimed reference metadata."""
        if not entry.doi:
            return

        try:
            url = f"{self.CROSSREF_API}{entry.doi}"
            resp = requests.get(url, headers=self.headers, timeout=5.0)

            if resp.status_code == 404:
                entry.verification_status = "UNRESOLVABLE"
                entry.issues.append("DOI not found in Crossref registry")
                return

            if resp.status_code != 200:
                entry.verification_status = "UNVERIFIED"
                entry.issues.append(f"Crossref returned HTTP {resp.status_code}")
                return

            data = resp.json().get("message", {})
            resolved_title = " ".join(data.get("title", []))
            
            # Check resolved authors
            resolved_authors = []
            for a in data.get("author", []):
                name = a.get("family", "") or a.get("name", "")
                if name:
                    resolved_authors.append(name)

            # Check year
            pub_year = None
            date_parts = data.get("published", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                pub_year = str(date_parts[0][0])

            # Validation logic
            sim = title_similarity(entry.parsed_title or "", resolved_title)
            auth_ok = author_match(entry.parsed_authors, resolved_authors)

            if sim < 0.20 and not auth_ok:
                # Total mismatch &rarr; Hallucinated reference
                entry.verification_status = "HALLUCINATED"
                entry.issues.append(
                    f"DOI resolves to completely different paper: '{resolved_title[:70]}...' by {', '.join(resolved_authors[:2])}"
                )
            elif sim < 0.50 or not auth_ok:
                entry.verification_status = "MISMATCH"
                if sim < 0.50:
                    entry.issues.append(f"Title discrepancy: resolves to '{resolved_title[:60]}...'")
                if not auth_ok:
                    entry.issues.append(f"Author discrepancy: resolves to {', '.join(resolved_authors[:2])}")
            else:
                entry.verification_status = "VALID"

        except Exception as e:
            logger.warning(f"Crossref lookup failed for DOI {entry.doi}: {e}")
            entry.verification_status = "UNVERIFIED"
            entry.issues.append(f"Lookup error: {e}")

    def _find_page(self, char_offset: int, pages: list) -> int:
        for p in pages:
            start = getattr(p, "char_start", 0)
            end = getattr(p, "char_end", 0)
            if start <= char_offset <= end:
                return getattr(p, "page_number", 1)
        return 1
