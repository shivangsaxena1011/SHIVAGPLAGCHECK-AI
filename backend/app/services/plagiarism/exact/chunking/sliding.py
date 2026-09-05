"""Sliding-window sentence chunker.

Adapted from Noplag Engine (Apache-2.0).
Generates overlapping chunks composed of sentences, recording character coordinates
relative to the parent document.
"""

from __future__ import annotations

from dataclasses import dataclass
from app.services.document.extractor import SentenceSpan


@dataclass(frozen=True)
class DocumentChunk:
    chunk_index: int
    char_start: int
    char_end: int
    page_number: int
    text: str
    sentences: list[SentenceSpan]


def chunk_sentences(
    sentences: list[SentenceSpan],
    window_size: int = 4,
    step_size: int = 2,
) -> list[DocumentChunk]:
    """Chunk a list of sentences into overlapping windows."""
    if not sentences:
        return []

    chunks: list[DocumentChunk] = []
    chunk_idx = 0
    total = len(sentences)

    for start_i in range(0, total, step_size):
        end_i = min(start_i + window_size, total)
        window = sentences[start_i:end_i]
        if not window:
            break

        c_start = window[0].char_start
        c_end = window[-1].char_end
        p_num = window[0].page_number
        combined_text = " ".join(s.text for s in window)

        chunks.append(
            DocumentChunk(
                chunk_index=chunk_idx,
                char_start=c_start,
                char_end=c_end,
                page_number=p_num,
                text=combined_text,
                sentences=window,
            )
        )
        chunk_idx += 1

        if end_i == total:
            break

    return chunks
