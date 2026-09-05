"""Score Fusion and Evidence Aggregation Engine.

Complies strictly with Section 7 and Section 24:
- Does NOT calculate a single cosine similarity as plagiarism.
- Combines separate evidence categories (EXACT, NEAR_EXACT, SEMANTIC, SELF_PLAGIARISM).
- Implements strict interval union logic so overlapping passages are NEVER double-counted.
- Handles exclusions: quotes, bibliography, small matches (< 10 words), citations.
- Calculates transparent source-by-source contributions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from app.schemas.evidence import MatchEvidenceSchema
from app.schemas.check import CheckOptions, SimilarityBreakdown, SourceContribution
from app.services.plagiarism.exact.intervals import (
    merge_intervals,
    subtract_intervals,
    calculate_coverage,
    total_interval_length,
)


@dataclass
class FusionResult:
    breakdown: SimilarityBreakdown
    source_contributions: list[SourceContribution]
    filtered_matches: list[MatchEvidenceSchema]
    score_explanation: dict[str, float | str]


class ScoreFusionEngine:
    """Combines evidence from exact alignment, semantic matching, and self-plagiarism."""

    MIN_WORDS_FOR_MATCH = 8  # Small match exclusion threshold

    def fuse(
        self,
        matches: list[MatchEvidenceSchema],
        total_chars: int,
        total_words: int,
        quote_spans: list[tuple[int, int]],
        bib_spans: list[tuple[int, int]],
        citation_spans: list[tuple[int, int]],
        options: CheckOptions,
    ) -> FusionResult:
        """Run deterministic score fusion across all match evidence."""
        if total_chars <= 0:
            return FusionResult(
                breakdown=SimilarityBreakdown(
                    overall_similarity=0.0,
                    exact_similarity=0.0,
                    near_exact_similarity=0.0,
                    semantic_similarity=0.0,
                    self_plagiarism_similarity=0.0,
                    matched_word_count=0,
                    total_words=0,
                ),
                source_contributions=[],
                filtered_matches=[],
                score_explanation={"overall": 0.0, "reason": "Empty document"},
            )

        # 1. Build exclusion intervals
        exclusions: list[tuple[int, int]] = []
        if options.exclude_quotes:
            exclusions.extend(quote_spans)
        if options.exclude_bibliography:
            exclusions.extend(bib_spans)
        if options.exclude_citations:
            exclusions.extend(citation_spans)

        merged_exclusions = merge_intervals(exclusions)

        # 2. Filter matches
        filtered_matches: list[MatchEvidenceSchema] = []
        for m in matches:
            # Small match filter
            word_count = len(m.submitted_text.split())
            if options.exclude_small_matches and word_count < self.MIN_WORDS_FOR_MATCH:
                continue

            # Exclusions filter: if match is entirely inside excluded spans, omit it
            m_interval = [(m.submission_start, m.submission_end)]
            remaining_after_excl = subtract_intervals(m_interval, merged_exclusions)
            if not remaining_after_excl:
                continue

            filtered_matches.append(m)

        # 3. Compute union intervals by category
        exact_intervals: list[tuple[int, int]] = []
        near_exact_intervals: list[tuple[int, int]] = []
        semantic_intervals: list[tuple[int, int]] = []
        self_plag_intervals: list[tuple[int, int]] = []
        all_intervals: list[tuple[int, int]] = []

        # Source-wise intervals
        source_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
        source_meta: dict[str, dict] = {}

        for m in filtered_matches:
            iv = (m.submission_start, m.submission_end)
            all_intervals.append(iv)

            if m.detection_type == "EXACT":
                exact_intervals.append(iv)
            elif m.detection_type == "NEAR_EXACT":
                near_exact_intervals.append(iv)
            elif m.detection_type == "SEMANTIC":
                semantic_intervals.append(iv)
            elif m.detection_type == "SELF_PLAGIARISM":
                self_plag_intervals.append(iv)

            src_key = m.source_id or "unknown"
            source_intervals[src_key].append(iv)
            if src_key not in source_meta:
                source_meta[src_key] = {
                    "title": m.title or "Unknown Source",
                    "authors": m.authors,
                    "url": m.url,
                    "doi": m.doi,
                    "source_type": m.source_type,
                    "primary_match_type": m.detection_type,
                }

        # Apply exclusions from final interval calculation
        cleaned_all = subtract_intervals(all_intervals, merged_exclusions)
        cleaned_exact = subtract_intervals(exact_intervals, merged_exclusions)
        cleaned_near_exact = subtract_intervals(near_exact_intervals, merged_exclusions)
        cleaned_semantic = subtract_intervals(semantic_intervals, merged_exclusions)
        cleaned_self_plag = subtract_intervals(self_plag_intervals, merged_exclusions)

        # 4. Compute coverage percentages (Strictly non-overlapping union)
        overall_sim = calculate_coverage(cleaned_all, total_chars)
        exact_sim = calculate_coverage(cleaned_exact, total_chars)
        near_exact_sim = calculate_coverage(cleaned_near_exact, total_chars)
        semantic_sim = calculate_coverage(cleaned_semantic, total_chars)
        self_plag_sim = calculate_coverage(cleaned_self_plag, total_chars)

        total_matched_chars = total_interval_length(cleaned_all)
        # Approximate matched words based on character proportion
        char_ratio = (total_matched_chars / total_chars) if total_chars > 0 else 0
        matched_words = int(round(total_words * char_ratio))

        excluded_quote_chars = total_interval_length(quote_spans)
        excluded_bib_chars = total_interval_length(bib_spans)

        breakdown = SimilarityBreakdown(
            overall_similarity=overall_sim,
            exact_similarity=exact_sim,
            near_exact_similarity=near_exact_sim,
            semantic_similarity=semantic_sim,
            self_plagiarism_similarity=self_plag_sim,
            matched_word_count=matched_words,
            total_words=total_words,
            excluded_quote_words=int(round(total_words * (excluded_quote_chars / max(total_chars, 1)))),
            excluded_bibliography_words=int(round(total_words * (excluded_bib_chars / max(total_chars, 1)))),
        )

        # 5. Compute per-source contributions
        source_contributions: list[SourceContribution] = []
        color_idx = 0

        for src_id, ivs in source_intervals.items():
            cleaned_src_ivs = subtract_intervals(ivs, merged_exclusions)
            src_cov = calculate_coverage(cleaned_src_ivs, total_chars)
            src_matched_chars = total_interval_length(cleaned_src_ivs)
            src_words = int(round(total_words * (src_matched_chars / max(total_chars, 1))))

            meta = source_meta[src_id]
            source_contributions.append(
                SourceContribution(
                    source_id=src_id,
                    title=meta["title"],
                    authors=meta["authors"],
                    url=meta["url"],
                    doi=meta["doi"],
                    source_type=meta["source_type"],
                    similarity_contribution=src_cov,
                    matched_words=src_words,
                    primary_match_type=meta["primary_match_type"],
                    color_index=color_idx,
                )
            )
            color_idx += 1

        # Sort sources by contribution descending
        source_contributions.sort(key=lambda x: -x.similarity_contribution)

        # Update per-match contribution score on filtered matches
        src_cov_lookup = {s.source_id: s.similarity_contribution for s in source_contributions}
        for m in filtered_matches:
            m.source_similarity_contribution = src_cov_lookup.get(m.source_id or "", 0.0)

        return FusionResult(
            breakdown=breakdown,
            source_contributions=source_contributions,
            filtered_matches=filtered_matches,
            score_explanation={
                "overall_similarity": overall_sim,
                "exact": exact_sim,
                "near_exact": near_exact_sim,
                "semantic": semantic_sim,
                "self_plagiarism": self_plag_sim,
                "total_matched_words": matched_words,
            },
        )
