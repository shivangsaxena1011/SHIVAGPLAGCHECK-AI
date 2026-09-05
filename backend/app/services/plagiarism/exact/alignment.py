"""L0 text alignment — seed-and-extend over query/candidate text pairs.

Adapted from Noplag Engine (Apache-2.0).
BLAST-adapted for natural language:
1. Seed — find maximal exact common substrings >= min_seed_len.
2. Extend — walk outward in 20-character windows while match ratio meets tolerance.
3. Merge + filter — combine passages along identical diagonals and drop sub-threshold lengths.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

_EXTEND_LOOKAHEAD = 20
_MERGE_GAP = 20
_QUERY_OVERLAP_DEDUPE_THRESHOLD = 0.5


@dataclass(frozen=True)
class AlignedPassage:
    query_start: int
    query_end: int
    candidate_start: int
    candidate_end: int
    score: float
    match_type: str = "EXACT"  # "EXACT" or "NEAR_EXACT"


def align(
    query: str,
    candidate: str,
    min_seed_len: int = 12,
    extend_tolerance: float = 0.75,
    min_passage_len: int = 15,
) -> list[AlignedPassage]:
    """Align query text against candidate text and return matched passages."""
    if len(query) < min_seed_len or len(candidate) < min_seed_len:
        return []

    seeds = _find_seeds(query, candidate, min_seed_len)
    if not seeds:
        return []

    passages: list[AlignedPassage] = []
    for q_start, c_start, length in seeds:
        q_end, c_end = _extend_right(query, candidate, q_start + length, c_start + length, extend_tolerance)
        q_begin, c_begin = _extend_left(query, candidate, q_start, c_start, extend_tolerance)
        
        aligned_q_len = q_end - q_begin
        aligned_c_len = c_end - c_begin
        if aligned_q_len >= min_passage_len and aligned_c_len >= min_passage_len:
            # Calculate match ratio
            matched_chars = sum(
                1 for i in range(min(aligned_q_len, aligned_c_len))
                if query[q_begin + i].lower() == candidate[c_begin + i].lower()
            )
            score = matched_chars / max(aligned_q_len, aligned_c_len)
            match_type = "EXACT" if score >= 0.95 else "NEAR_EXACT"

            passages.append(
                AlignedPassage(
                    query_start=q_begin,
                    query_end=q_end,
                    candidate_start=c_begin,
                    candidate_end=c_end,
                    score=round(score, 3),
                    match_type=match_type,
                )
            )

    merged = _merge_passages(passages)
    return _dedupe_query_overlaps(merged)


def _find_seeds(query: str, candidate: str, min_seed_len: int) -> list[tuple[int, int, int]]:
    """Index candidate k-grams in a dict and lookup seeds from query."""
    index: dict[str, list[int]] = defaultdict(list)
    cand_norm = candidate.lower()
    query_norm = query.lower()

    for i in range(len(cand_norm) - min_seed_len + 1):
        kgram = cand_norm[i : i + min_seed_len]
        index[kgram].append(i)

    seeds: list[tuple[int, int, int]] = []
    seen_seeds: set[tuple[int, int]] = set()

    q_idx = 0
    while q_idx <= len(query_norm) - min_seed_len:
        kgram = query_norm[q_idx : q_idx + min_seed_len]
        if kgram in index:
            for c_pos in index[kgram]:
                # Verify exact character match
                seed_key = (q_idx, c_pos)
                if seed_key in seen_seeds:
                    continue
                
                # Extend maximal exact match
                length = min_seed_len
                while (
                    q_idx + length < len(query_norm)
                    and c_pos + length < len(cand_norm)
                    and query_norm[q_idx + length] == cand_norm[c_pos + length]
                ):
                    length += 1

                seeds.append((q_idx, c_pos, length))
                seen_seeds.add(seed_key)
            q_idx += max(1, min_seed_len // 2)
        else:
            q_idx += 1

    return seeds


def _extend_right(query: str, candidate: str, q_pos: int, c_pos: int, tolerance: float) -> tuple[int, int]:
    """Walk outward right in lookahead windows."""
    q_len = len(query)
    c_len = len(candidate)

    while q_pos < q_len and c_pos < c_len:
        step = min(_EXTEND_LOOKAHEAD, q_len - q_pos, c_len - c_pos)
        if step <= 0:
            break
        matches = sum(
            1 for i in range(step)
            if query[q_pos + i].lower() == candidate[c_pos + i].lower()
        )
        if (matches / step) >= tolerance:
            q_pos += step
            c_pos += step
        else:
            # Single char check to advance to exact edge
            while q_pos < q_len and c_pos < c_len and query[q_pos].lower() == candidate[c_pos].lower():
                q_pos += 1
                c_pos += 1
            break
    return q_pos, c_pos


def _extend_left(query: str, candidate: str, q_pos: int, c_pos: int, tolerance: float) -> tuple[int, int]:
    """Walk outward left in lookahead windows."""
    while q_pos > 0 and c_pos > 0:
        step = min(_EXTEND_LOOKAHEAD, q_pos, c_pos)
        if step <= 0:
            break
        matches = sum(
            1 for i in range(step)
            if query[q_pos - step + i].lower() == candidate[c_pos - step + i].lower()
        )
        if (matches / step) >= tolerance:
            q_pos -= step
            c_pos -= step
        else:
            while q_pos > 0 and c_pos > 0 and query[q_pos - 1].lower() == candidate[c_pos - 1].lower():
                q_pos -= 1
                c_pos -= 1
            break
    return q_pos, c_pos


def _merge_passages(passages: list[AlignedPassage]) -> list[AlignedPassage]:
    """Merge passages lying on identical diagonals (c_start - q_start)."""
    if not passages:
        return []

    diagonals: dict[int, list[AlignedPassage]] = defaultdict(list)
    for p in passages:
        diag = p.candidate_start - p.query_start
        diagonals[diag].append(p)

    merged: list[AlignedPassage] = []
    for diag, diag_passages in diagonals.items():
        sorted_p = sorted(diag_passages, key=lambda x: x.query_start)
        cur = sorted_p[0]

        for nxt in sorted_p[1:]:
            if nxt.query_start <= cur.query_end + _MERGE_GAP:
                cur = AlignedPassage(
                    query_start=cur.query_start,
                    query_end=max(cur.query_end, nxt.query_end),
                    candidate_start=cur.candidate_start,
                    candidate_end=max(cur.candidate_end, nxt.candidate_end),
                    score=round((cur.score + nxt.score) / 2.0, 3),
                    match_type="EXACT" if (cur.match_type == "EXACT" and nxt.match_type == "EXACT") else "NEAR_EXACT",
                )
            else:
                merged.append(cur)
                cur = nxt
        merged.append(cur)

    return sorted(merged, key=lambda x: x.query_start)


def _dedupe_query_overlaps(passages: list[AlignedPassage]) -> list[AlignedPassage]:
    """Retain highest-scoring passage when candidate alignments overlap query regions."""
    if not passages:
        return []

    sorted_p = sorted(passages, key=lambda x: (-(x.query_end - x.query_start), -x.score))
    kept: list[AlignedPassage] = []

    for p in sorted_p:
        p_len = p.query_end - p.query_start
        overlap_found = False
        for k in kept:
            # Overlap interval
            ov_start = max(p.query_start, k.query_start)
            ov_end = min(p.query_end, k.query_end)
            if ov_start < ov_end:
                overlap_fraction = (ov_end - ov_start) / p_len
                if overlap_fraction > _QUERY_OVERLAP_DEDUPE_THRESHOLD:
                    overlap_found = True
                    break
        if not overlap_found:
            kept.append(p)

    return sorted(kept, key=lambda x: x.query_start)
