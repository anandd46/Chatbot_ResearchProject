"""
Score Fusion
============
Implements configurable multi-signal score fusion:

  final_score = α·tfidf + β·word_order + γ·intent + δ·keyword

Weights α, β, γ, δ are loaded from the database (nlp_settings table)
at runtime and can be changed by the admin without restarting the server.

Engineering decision: weights are normalized if they don't sum to 1.0,
so the admin can input arbitrary positive values and the system remains valid.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.nlp.word_order_vector import word_order_similarity


@dataclass
class FusionWeights:
    tfidf: float = 0.40
    word_order: float = 0.25
    intent: float = 0.20
    keyword: float = 0.15

    def normalized(self) -> "FusionWeights":
        total = self.tfidf + self.word_order + self.intent + self.keyword
        if total == 0:
            return FusionWeights(0.25, 0.25, 0.25, 0.25)
        return FusionWeights(
            self.tfidf / total,
            self.word_order / total,
            self.intent / total,
            self.keyword / total,
        )


def compute_keyword_score(query_lemmas: List[str], entry_keywords: List[str]) -> float:
    """Jaccard-like overlap between query lemmas and KB entry keywords."""
    if not entry_keywords or not query_lemmas:
        return 0.0
    query_set = set(q.lower() for q in query_lemmas)
    kw_set = set(k.lower() for k in entry_keywords)
    intersection = query_set & kw_set
    union = query_set | kw_set
    return len(intersection) / len(union) if union else 0.0


def compute_intent_score(detected_intent: str, entry_category: str) -> float:
    """Returns 1.0 if detected intent matches entry category, else 0.0."""
    if detected_intent == "unknown":
        return 0.0
    return 1.0 if detected_intent.lower() == entry_category.lower() else 0.0


def fuse_scores(
    query_tokens: List[str],
    entry: Dict,
    tfidf_score: float,
    detected_intent: str,
    weights: FusionWeights,
) -> Dict:
    """
    Compute all component scores and the final fused score for one KB entry.

    Returns:
      tfidf_score, word_order_score, intent_score, keyword_score, final_score
    """
    w = weights.normalized()

    # Word Order Vector similarity
    entry_tokens = entry.get("question", "").lower().split()
    wo_score = word_order_similarity(query_tokens, entry_tokens)

    # Intent score
    intent_score = compute_intent_score(detected_intent, entry.get("category", ""))

    # Keyword overlap score
    kw_score = compute_keyword_score(query_tokens, entry.get("keywords") or [])

    # Weighted fusion
    final = (
        w.tfidf * tfidf_score
        + w.word_order * wo_score
        + w.intent * intent_score
        + w.keyword * kw_score
    )

    return {
        "tfidf_score": round(tfidf_score, 4),
        "word_order_score": round(wo_score, 4),
        "intent_score": round(intent_score, 4),
        "keyword_score": round(kw_score, 4),
        "final_score": round(final, 4),
    }
