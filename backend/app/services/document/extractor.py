"""Document Processing Service.

Extracts text from PDF, DOCX, and TXT files, accurately preserving:
- Page numbers
- Paragraph indices
- Sentence boundaries
- Character start and end offsets relative to the full document
- Identification of quotes and bibliography sections.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import pypdf
import docx

# PyMuPDF import (prefer modern pymupdf over legacy fitz)
try:
    import pymupdf as fitz
    HAS_PYMUPDF = True
except ImportError:
    try:
        import fitz
        HAS_PYMUPDF = True
    except ImportError:
        HAS_PYMUPDF = False


@dataclass
class SentenceSpan:
    sentence_index: int
    paragraph_index: int
    page_number: int
    char_start: int
    char_end: int
    text: str


@dataclass
class PageSpan:
    page_number: int
    char_start: int
    char_end: int
    text: str


@dataclass
class SectionSpan:
    section_type: str  # "TITLE", "BODY", "QUOTE", "BIBLIOGRAPHY"
    title: str | None
    char_start: int
    char_end: int


@dataclass
class ExtractedDocument:
    raw_text: str
    word_count: int
    char_count: int
    page_count: int
    pages: list[PageSpan] = field(default_factory=list)
    sentences: list[SentenceSpan] = field(default_factory=list)
    sections: list[SectionSpan] = field(default_factory=list)
    metadata: dict[str, str | int] = field(default_factory=dict)


class DocumentExtractor:
    """Multi-format document extractor preserving exact positional mappings."""

    BIBLIOGRAPHY_HEADERS = re.compile(
        r"^(?:references|bibliography|works\s+cited|literature\s+cited)\b",
        re.IGNORECASE,
    )

    QUOTE_PATTERN = re.compile(
        r'["“«]([^"”»]{15,})["”»]',
        re.MULTILINE,
    )

    SENTENCE_SPLIT_RE = re.compile(
        r'(?<=[.!?])\s+(?=[A-Z0-9"“])'
    )

    def extract_file(self, file_path: Path | str) -> ExtractedDocument:
        """Extract a document from a file path."""
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")
        with open(path, "rb") as f:
            return self.extract(f, ext, path.name)

    def extract(self, file_obj: BinaryIO | bytes, file_type: str, filename: str = "document") -> ExtractedDocument:
        """Extract from a file-like object or bytes."""
        if isinstance(file_obj, bytes):
            stream = io.BytesIO(file_obj)
        else:
            stream = file_obj

        ext = file_type.lower().lstrip(".")
        if ext == "pdf":
            return self._extract_pdf(stream, filename)
        elif ext == "docx":
            return self._extract_docx(stream, filename)
        elif ext == "txt":
            return self._extract_txt(stream, filename)
        else:
            raise ValueError(f"Unsupported file format: .{ext}")

    def _extract_pdf(self, stream: io.BytesIO, filename: str) -> ExtractedDocument:
        """Extract text from PDF preserving page boundaries."""
        pages: list[PageSpan] = []
        full_text_parts: list[str] = []
        current_offset = 0

        # Prefer PyMuPDF if available, fallback to pypdf
        if HAS_PYMUPDF:
            stream.seek(0)
            doc = fitz.open(stream=stream.read(), filetype="pdf")
            page_count = len(doc)
            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]
                page_text = page.get_text() or ""
                # Normalize text
                page_text = unicodedata.normalize("NFKC", page_text)
                p_len = len(page_text)
                pages.append(
                    PageSpan(
                        page_number=page_num,
                        char_start=current_offset,
                        char_end=current_offset + p_len,
                        text=page_text,
                    )
                )
                full_text_parts.append(page_text)
                current_offset += p_len + 1  # newline between pages
            doc.close()
        else:
            stream.seek(0)
            reader = pypdf.PdfReader(stream)
            page_count = len(reader.pages)
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                page_text = page.extract_text() or ""
                page_text = unicodedata.normalize("NFKC", page_text)
                p_len = len(page_text)
                pages.append(
                    PageSpan(
                        page_number=page_num,
                        char_start=current_offset,
                        char_end=current_offset + p_len,
                        text=page_text,
                    )
                )
                full_text_parts.append(page_text)
                current_offset += p_len + 1

        full_text = "\n".join(full_text_parts)
        return self._build_document(full_text, pages, {"filename": filename, "type": "pdf"})

    def _extract_docx(self, stream: io.BytesIO, filename: str) -> ExtractedDocument:
        """Extract text from DOCX preserving paragraph structure and estimating pages."""
        stream.seek(0)
        doc = docx.Document(stream)
        full_text_parts: list[str] = []
        current_offset = 0
        pages: list[PageSpan] = []

        # In Word, page boundaries are rendered dynamically; we estimate ~450 words or 2500 chars per page
        CHARS_PER_PAGE = 2500
        paragraphs_text = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs_text)
        full_text = unicodedata.normalize("NFKC", full_text)

        total_chars = len(full_text)
        if total_chars == 0:
            pages.append(PageSpan(page_number=1, char_start=0, char_end=0, text=""))
        else:
            page_num = 1
            start = 0
            while start < total_chars:
                end = min(start + CHARS_PER_PAGE, total_chars)
                # Try to break at newline or period if possible
                if end < total_chars:
                    next_break = full_text.rfind("\n", start, end)
                    if next_break != -1 and next_break > start + 1000:
                        end = next_break + 1
                pages.append(
                    PageSpan(
                        page_number=page_num,
                        char_start=start,
                        char_end=end,
                        text=full_text[start:end],
                    )
                )
                page_num += 1
                start = end

        return self._build_document(full_text, pages, {"filename": filename, "type": "docx"})

    def _extract_txt(self, stream: io.BytesIO, filename: str) -> ExtractedDocument:
        """Extract plain text file with pagination mapping."""
        stream.seek(0)
        raw_bytes = stream.read()
        try:
            full_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            full_text = raw_bytes.decode("latin-1", errors="replace")

        full_text = unicodedata.normalize("NFKC", full_text)
        pages: list[PageSpan] = []
        CHARS_PER_PAGE = 2500
        total_chars = len(full_text)

        if total_chars == 0:
            pages.append(PageSpan(page_number=1, char_start=0, char_end=0, text=""))
        else:
            page_num = 1
            start = 0
            while start < total_chars:
                end = min(start + CHARS_PER_PAGE, total_chars)
                pages.append(
                    PageSpan(
                        page_number=page_num,
                        char_start=start,
                        char_end=end,
                        text=full_text[start:end],
                    )
                )
                page_num += 1
                start = end

        return self._build_document(full_text, pages, {"filename": filename, "type": "txt"})

    def _build_document(
        self,
        full_text: str,
        pages: list[PageSpan],
        metadata: dict[str, str | int],
    ) -> ExtractedDocument:
        """Construct structured document with sentence and section segmentations."""
        words = full_text.split()
        word_count = len(words)
        char_count = len(full_text)
        page_count = max(len(pages), 1)

        # 1. Segment sentences and track coordinates
        sentences: list[SentenceSpan] = []
        paragraph_index = 0
        sentence_global_index = 0

        # Split into paragraphs by double newlines or single newlines
        paragraphs = re.split(r"\n\s*\n|\r\n\s*\r\n", full_text)
        running_char = 0

        for p_idx, para in enumerate(paragraphs):
            para_text = para.strip()
            if not para_text:
                continue
            
            # Locate paragraph in full text
            p_start = full_text.find(para, running_char)
            if p_start == -1:
                p_start = running_char
            p_end = p_start + len(para)
            running_char = p_end

            # Determine page for paragraph start
            p_page = 1
            for page in pages:
                if page.char_start <= p_start <= page.char_end:
                    p_page = page.page_number
                    break

            # Sentence splitting
            raw_sents = self.SENTENCE_SPLIT_RE.split(para_text)
            sent_local_start = p_start

            for s in raw_sents:
                clean_s = s.strip()
                if not clean_s:
                    continue
                s_start = full_text.find(clean_s, sent_local_start)
                if s_start == -1:
                    s_start = sent_local_start
                s_end = s_start + len(clean_s)
                sent_local_start = s_end

                # Find page for this sentence
                s_page = p_page
                for page in pages:
                    if page.char_start <= s_start <= page.char_end:
                        s_page = page.page_number
                        break

                sentences.append(
                    SentenceSpan(
                        sentence_index=sentence_global_index,
                        paragraph_index=p_idx,
                        page_number=s_page,
                        char_start=s_start,
                        char_end=s_end,
                        text=clean_s,
                    )
                )
                sentence_global_index += 1

        # 2. Detect Sections (Quotes, Bibliography)
        sections: list[SectionSpan] = []

        # Find quotes
        for match in self.QUOTE_PATTERN.finditer(full_text):
            q_start = match.start()
            q_end = match.end()
            sections.append(
                SectionSpan(
                    section_type="QUOTE",
                    title="Direct Quotation",
                    char_start=q_start,
                    char_end=q_end,
                )
            )

        # Detect Bibliography / References section
        lines = full_text.splitlines(keepends=True)
        cur_offset = 0
        bib_start = None
        for line in lines:
            line_str = line.strip()
            if self.BIBLIOGRAPHY_HEADERS.match(line_str) and len(line_str) < 50:
                bib_start = cur_offset
                break
            cur_offset += len(line)

        if bib_start is not None:
            sections.append(
                SectionSpan(
                    section_type="BIBLIOGRAPHY",
                    title="References / Bibliography",
                    char_start=bib_start,
                    char_end=len(full_text),
                )
            )

        return ExtractedDocument(
            raw_text=full_text,
            word_count=word_count,
            char_count=char_count,
            page_count=page_count,
            pages=pages,
            sentences=sentences,
            sections=sections,
            metadata=metadata,
        )
