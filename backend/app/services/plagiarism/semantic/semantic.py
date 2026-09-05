"""Semantic similarity detector using Sentence Transformers (SBERT).

Adapted from Aegis Integrity (MIT).
Detects concept-level paraphrasing where phrasing is rewritten but meaning is retained.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticMatch:
    query_sentence: str
    query_start: int
    query_end: int
    page_number: int
    source_id: str
    source_title: str
    source_sentence: str
    cosine_score: float
    is_paraphrase: bool


class SemanticDetector:
    """Dense semantic similarity detector using Sentence Transformers embeddings."""

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        cosine_threshold: float = 0.82,
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.cosine_threshold = cosine_threshold
        self.device = device
        self._model = None

    def _get_model(self):
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except Exception as e:
                logger.warning(f"SentenceTransformer not available ({e}). Using TF-IDF/statistical semantic fallback.")
                self._model = None
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of text strings into normalized dense vectors."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        model = self._get_model()
        if model is not None:
            embeddings = model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return np.asarray(embeddings, dtype=np.float32)
        else:
            # Fallback: Character n-gram vectorization with TF-IDF weighting
            return self._statistical_embed(texts)

    def _statistical_embed(self, texts: list[str]) -> np.ndarray:
        """Lightweight bag-of-words / TF-IDF embedding fallback when torch model is absent."""
        vocab: dict[str, int] = {}
        for t in texts:
            for word in t.lower().split():
                if len(word) > 2 and word not in vocab:
                    vocab[word] = len(vocab)

        dim = max(len(vocab), 1)
        matrix = np.zeros((len(texts), dim), dtype=np.float32)

        for i, t in enumerate(texts):
            for word in t.lower().split():
                if word in vocab:
                    matrix[i, vocab[word]] += 1.0
            norm = np.linalg.norm(matrix[i])
            if norm > 0:
                matrix[i] /= norm

        return matrix

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix between two sets of normalized embeddings."""
        if vec_a.size == 0 or vec_b.size == 0:
            return np.empty((0, 0), dtype=np.float32)
        # Assuming vectors are L2-normalized: dot product equals cosine similarity
        return np.dot(vec_a, vec_b.T)

    def find_matches(
        self,
        query_sentences: list[dict],
        source_id: str,
        source_title: str,
        candidate_sentences: list[str],
        top_k: int = 3,
    ) -> list[SemanticMatch]:
        """Compare query sentences against candidate source sentences."""
        if not query_sentences or not candidate_sentences:
            return []

        # Filter out very short sentences
        valid_queries = [
            q for q in query_sentences
            if len(q["text"].split()) >= 6
        ]
        valid_candidates = [
            c for c in candidate_sentences
            if len(c.split()) >= 6
        ]

        if not valid_queries or not valid_candidates:
            return []

        q_texts = [q["text"] for q in valid_queries]
        q_vecs = self.encode(q_texts)
        c_vecs = self.encode(valid_candidates)

        sim_matrix = self.compute_similarity(q_vecs, c_vecs)

        matches: list[SemanticMatch] = []
        for i, q in enumerate(valid_queries):
            best_cand_idx = int(np.argmax(sim_matrix[i]))
            best_score = float(sim_matrix[i, best_cand_idx])

            if best_score >= self.cosine_threshold:
                matches.append(
                    SemanticMatch(
                        query_sentence=q["text"],
                        query_start=q["char_start"],
                        query_end=q["char_end"],
                        page_number=q.get("page_number", 1),
                        source_id=source_id,
                        source_title=source_title,
                        source_sentence=valid_candidates[best_cand_idx],
                        cosine_score=round(best_score, 3),
                        is_paraphrase=True,
                    )
                )

        return matches
