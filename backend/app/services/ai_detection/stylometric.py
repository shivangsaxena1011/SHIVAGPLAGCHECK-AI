"""Stylometric feature extraction for AI and authorship analysis.

Adapted from Aegis Integrity (MIT).
Computes:
- Type-Token Ratio (vocabulary richness)
- Hapax Legomena ratio (words occurring exactly once)
- Sentence length mean and standard deviation (syntactic burstiness)
- Passive voice indicator density
- Nominalization density (-tion, -ment, -ance suffixes)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass
class StylometricProfile:
    word_count: int
    sentence_count: int
    type_token_ratio: float
    hapax_legomena_ratio: float
    sentence_len_mean: float
    sentence_len_std: float
    passive_voice_density: float
    nominalization_density: float


class StylometricAnalyzer:
    """Computes academic stylometric measurements."""

    PASSIVE_RE = re.compile(
        r"\b(?:is|are|was|were|been|being|be)\s+([a-z]+ed|[a-z]+en|shown|found|seen|given|made|observed|obtained)\b",
        re.IGNORECASE,
    )

    NOMINALIZATION_RE = re.compile(
        r"\b[a-z]{4,}(?:tion|tions|ment|ments|ance|ances|ence|ences|ity|ities)\b",
        re.IGNORECASE,
    )

    def analyze(self, text: str, sentences: list[str] | None = None) -> StylometricProfile:
        """Analyze text and extract stylometric metrics."""
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        word_count = len(words)
        if word_count == 0:
            return StylometricProfile(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        # 1. Type-Token Ratio
        unique_words = set(words)
        ttr = len(unique_words) / word_count

        # 2. Hapax Legomena
        word_freq: dict[str, int] = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        hapax_count = sum(1 for count in word_freq.values() if count == 1)
        hapax_ratio = hapax_count / word_count

        # 3. Sentence Length Statistics
        if sentences is None or len(sentences) == 0:
            sentences = re.split(r"[.!?]+\s+", text)
        clean_sents = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(len(clean_sents), 1)

        sent_lens = [len(re.findall(r"\b[a-zA-Z]+\b", s)) for s in clean_sents]
        mean_len = sum(sent_lens) / sentence_count
        variance = sum((l - mean_len) ** 2 for l in sent_lens) / sentence_count
        std_len = math.sqrt(variance)

        # 4. Passive Voice
        passive_matches = len(self.PASSIVE_RE.findall(text))
        passive_density = (passive_matches / sentence_count) if sentence_count > 0 else 0.0

        # 5. Nominalizations
        nom_matches = len(self.NOMINALIZATION_RE.findall(text))
        nom_density = (nom_matches / word_count) if word_count > 0 else 0.0

        return StylometricProfile(
            word_count=word_count,
            sentence_count=sentence_count,
            type_token_ratio=round(ttr, 4),
            hapax_legomena_ratio=round(hapax_ratio, 4),
            sentence_len_mean=round(mean_len, 2),
            sentence_len_std=round(std_len, 2),
            passive_voice_density=round(passive_density, 4),
            nominalization_density=round(nom_density, 4),
        )
