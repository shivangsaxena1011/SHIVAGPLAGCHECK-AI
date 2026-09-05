"""Interval manipulation and coverage helpers.

Adapted and extended from Noplag Engine (Apache-2.0).
Intervals are half-open: [start, end).
"""

from __future__ import annotations


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or adjoining half-open `(start, end)` intervals."""
    if not intervals:
        return []
    sorted_iv = sorted(intervals)
    merged: list[tuple[int, int]] = [sorted_iv[0]]
    for start, end in sorted_iv[1:]:
        if start > end:
            continue
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def subtract_intervals(
    base: list[tuple[int, int]],
    to_remove: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Subtract `to_remove` intervals from `base` intervals.

    Used to deduct quotes, bibliography, and boilerplate from detected matches.
    """
    merged_base = merge_intervals(base)
    merged_remove = merge_intervals(to_remove)

    result: list[tuple[int, int]] = []
    for b_start, b_end in merged_base:
        current_pieces = [(b_start, b_end)]
        for r_start, r_end in merged_remove:
            new_pieces = []
            for c_start, c_end in current_pieces:
                # No overlap
                if r_end <= c_start or r_start >= c_end:
                    new_pieces.append((c_start, c_end))
                else:
                    # Left piece
                    if c_start < r_start:
                        new_pieces.append((c_start, r_start))
                    # Right piece
                    if r_end < c_end:
                        new_pieces.append((r_end, c_end))
            current_pieces = new_pieces
        result.extend(current_pieces)

    return merge_intervals(result)


def total_interval_length(intervals: list[tuple[int, int]]) -> int:
    """Compute the non-overlapping covered length of a list of intervals."""
    merged = merge_intervals(intervals)
    return sum(end - start for start, end in merged if end > start)


def calculate_coverage(intervals: list[tuple[int, int]], total_length: int) -> float:
    """Compute percentage coverage (0.0 - 100.0) over total_length."""
    if total_length <= 0:
        return 0.0
    covered = total_interval_length(intervals)
    return min(100.0, round((covered / total_length) * 100.0, 2))
