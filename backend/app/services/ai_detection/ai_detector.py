"""Language-Calibrated AI Content Detector.

Adapted from Aegis Integrity (MIT).
Features:
- Multi-signal ensemble: Stylometric profile, burstiness, vocabulary richness, dual-tier GPT lexical tells.
- Sentence-level and paragraph-level scoring.
- ESL calibration (Liang et al., Stanford 2023) to eliminate false-positive bias against non-native writers.
- Strictly probabilistic likelihood outputs ("Estimated AI-writing likelihood", never claims certainty).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from app.services.ai_detection.stylometric import StylometricAnalyzer

logger = logging.getLogger(__name__)

# Tier 1: Strong AI lexical markers (infrequent in human technical prose, highly recurring in LLMs)
GPT_TELL_PHRASES_STRONG = [
    "delve into", "delves into", "delving into", "boasts", "underscores",
    "underscore", "in the realm of", "realm of", "testament to", "a testament",
    "navigate the complexities", "navigating the complexities", "tapestry of",
    "harness the power", "unlock the potential", "vital role in", "pivotal role",
    "sheds light on", "shed light on", "beacon of", "ever-evolving", "multifaceted",
    "seamlessly integrate", "embark on", "in summary,", "in essence,",
]

# Tier 2: Weak AI transitional markers (common academic words that LLMs overuse)
GPT_TELL_PHRASES_WEAK = [
    "furthermore,", "moreover,", "additionally,", "consequently,",
    "crucial to note", "notably,", "imperative", "paramount", "foster a",
    "testament", "comprehensive understanding", "interplay between",
]

# ESL Calibration multipliers (Liang et al., Stanford 2023)
# Raises the threshold before flagging non-native writing styles
ESL_THRESHOLD_MULTIPLIER = {
    "esl": 1.20,
    "native": 1.00,
}


@dataclass
class SentenceAISignal:
    sentence_index: int
    sentence_text: str
    char_start: int
    char_end: int
    page_number: int
    likelihood: float  # 0.0 - 1.0 (e.g. 0.71 = 71%)
    confidence: float
    primary_signal: str
    strong_tells: list[str] = field(default_factory=list)
    weak_tells: list[str] = field(default_factory=list)


@dataclass
class AIDetectionResult:
    overall_likelihood: float  # Percentage (0.0 - 100.0)
    confidence_band: str  # "High Confidence", "Moderate Confidence", "Low Confidence"
    high_signal_count: int  # Likelihood >= 0.65
    medium_signal_count: int  # Likelihood 0.40 - 0.64
    low_signal_count: int  # Likelihood < 0.40
    total_sentences: int
    sentence_signals: list[SentenceAISignal]
    methodology: str


class AIContentDetector:
    """Ensemble detector estimating AI writing probability across sentences and documents."""

    def __init__(self, author_style: str = "native"):
        self.stylometric_analyzer = StylometricAnalyzer()
        self.esl_multiplier = ESL_THRESHOLD_MULTIPLIER.get(author_style, 1.0)

    def analyze_document(
        self,
        full_text: str,
        sentences: list[dict],
    ) -> AIDetectionResult:
        """Analyze document sentences and aggregate multi-signal AI likelihood."""
        if not sentences:
            return AIDetectionResult(
                overall_likelihood=0.0,
                confidence_band="Insufficient Data",
                high_signal_count=0,
                medium_signal_count=0,
                low_signal_count=0,
                total_sentences=0,
                sentence_signals=[],
                methodology="Stylometric and lexical tell ensemble.",
            )

        # 1. Compute document-wide stylometric baseline
        sentence_texts = [s["text"] for s in sentences]
        profile = self.stylometric_analyzer.analyze(full_text, sentence_texts)

        # Uniform sentence length flag (AI tends to have very uniform sentence lengths, std < 6.0)
        low_burstiness = profile.sentence_len_std < 7.0 and len(sentences) > 5

        # 2. Evaluate each sentence
        sentence_signals: list[SentenceAISignal] = []
        sentence_scores: list[float] = []

        for idx, s in enumerate(sentences):
            text = s["text"]
            text_lower = text.lower()
            words = text.split()
            word_count = len(words)

            if word_count < 4:
                # Too short for meaningful detection
                sentence_signals.append(
                    SentenceAISignal(
                        sentence_index=s.get("sentence_index", idx),
                        sentence_text=text,
                        char_start=s["char_start"],
                        char_end=s["char_end"],
                        page_number=s.get("page_number", 1),
                        likelihood=0.15,
                        confidence=0.5,
                        primary_signal="Short segment: baseline likelihood",
                    )
                )
                sentence_scores.append(0.15)
                continue

            # Check lexical tells
            matched_strong = [phrase for phrase in GPT_TELL_PHRASES_STRONG if phrase in text_lower]
            matched_weak = [phrase for phrase in GPT_TELL_PHRASES_WEAK if phrase in text_lower]

            # Base likelihood from length uniformity
            score = 0.25  # default human baseline

            # Factor A: Lexical tells
            if matched_strong:
                score += len(matched_strong) * 0.28
            if matched_weak:
                score += len(matched_weak) * 0.12

            # Factor B: Low burstiness penalty
            if low_burstiness and 12 <= word_count <= 28:
                score += 0.15

            # Factor C: Repetitive syntactical cadence (passive voice + nominalization)
            if profile.nominalization_density > 0.10:
                score += 0.08

            # Apply ESL calibration (raises the threshold before a sentence is considered high risk)
            calibrated_score = score / self.esl_multiplier
            final_likelihood = max(0.05, min(0.95, round(calibrated_score, 3)))
            sentence_scores.append(final_likelihood)

            # Determine primary reasoning signal
            if matched_strong:
                reason = f"Contains strong LLM transition phrase: '{matched_strong[0]}'"
            elif final_likelihood >= 0.65 and low_burstiness:
                reason = "Unusually uniform syntactic cadence with low burstiness"
            elif matched_weak:
                reason = f"Elevated formal connective density ('{matched_weak[0]}')"
            elif final_likelihood < 0.35:
                reason = "Natural human-style lexical variance and burstiness"
            else:
                reason = "Moderate stylometric consistency"

            sentence_signals.append(
                SentenceAISignal(
                    sentence_index=s.get("sentence_index", idx),
                    sentence_text=text,
                    char_start=s["char_start"],
                    char_end=s["char_end"],
                    page_number=s.get("page_number", 1),
                    likelihood=final_likelihood,
                    confidence=0.82 if matched_strong else 0.70,
                    primary_signal=reason,
                    strong_tells=matched_strong,
                    weak_tells=matched_weak,
                )
            )

        # 3. Aggregate Document Score
        # Weight top 25% most suspect sentences more heavily to catch hybrid/injected text
        sorted_scores = sorted(sentence_scores, reverse=True)
        top_k = max(1, len(sorted_scores) // 4)
        top_avg = sum(sorted_scores[:top_k]) / top_k
        overall_avg = sum(sentence_scores) / len(sentence_scores)
        
        # Hybrid formula: 60% overall average + 40% top suspect average
        doc_likelihood_raw = (overall_avg * 0.60) + (top_avg * 0.40)
        overall_percentage = round(doc_likelihood_raw * 100.0, 1)

        high_signals = sum(1 for s in sentence_scores if s >= 0.65)
        med_signals = sum(1 for s in sentence_scores if 0.40 <= s < 0.65)
        low_signals = sum(1 for s in sentence_scores if s < 0.40)

        # Confidence band
        if high_signals > 5 or overall_percentage > 70.0:
            conf_band = "High Signal Confidence"
        elif med_signals > 5 or overall_percentage > 35.0:
            conf_band = "Moderate Signal Confidence"
        else:
            conf_band = "Low Concern / Natural Variation"

        return AIDetectionResult(
            overall_likelihood=overall_percentage,
            confidence_band=conf_band,
            high_signal_count=high_signals,
            medium_signal_count=med_signals,
            low_signal_count=low_signals,
            total_sentences=len(sentence_signals),
            sentence_signals=sentence_signals,
            methodology=(
                "Ensemble stylometry, burstiness variance, ESL calibration, and dual-tier "
                "lexical tell analysis. Automated statistical estimate, not definitive proof."
            ),
        )
