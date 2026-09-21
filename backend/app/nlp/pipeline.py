"""
NLP Pipeline Orchestrator
=========================
Ties together all NLP components and returns a full result dict
including a complete debug trace for the NLP Inspector.

Pipeline steps:
  1. Preprocess (normalize, tokenize, lemmatize, POS tag)
  2. WordNet expansion
  3. Intent classification
  4. TF-IDF candidate retrieval
  5. Score fusion (per candidate)
  6. Domain detection
  7. Response selection
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.nlp.domain_detector import detect_query_type
from app.nlp.intent_classifier import classify_intent
from app.nlp.preprocessor import preprocess
from app.nlp.retriever import get_candidates, get_tfidf_scores
from app.nlp.score_fusion import FusionWeights, fuse_scores
from app.nlp.wordnet_expander import expand_with_wordnet

logger = get_logger(__name__)

COLLEGE_NAME = settings.COLLEGE_NAME


def run_pipeline(
    query: str,
    weights: Optional[FusionWeights] = None,
    top_k: int = 5,
    baseline_mode: bool = False,
) -> Dict[str, Any]:
    """
    Run the full NLP pipeline.

    Args:
        query: Raw user input
        weights: Score fusion weights (from DB); uses defaults if None
        top_k: Number of candidates to retrieve
        baseline_mode: If True, use TF-IDF only (α=1, β=γ=δ=0)

    Returns a comprehensive dict with:
        - response: str (the answer to show the user)
        - intent: str
        - intent_score: float
        - tfidf_score: float
        - word_order_score: float
        - keyword_score: float
        - final_score: float
        - confidence: float
        - query_type: str (ANSWERED | UNKNOWN_INSTITUTIONAL | OUT_OF_DOMAIN)
        - kb_entry_id: Optional[str]
        - processing_time_ms: int
        - debug: dict (full pipeline trace for NLP Inspector)
    """
    t_start = time.perf_counter()

    if weights is None:
        weights = FusionWeights(
            tfidf=settings.SCORE_WEIGHT_TFIDF,
            word_order=settings.SCORE_WEIGHT_WORD_ORDER,
            intent=settings.SCORE_WEIGHT_INTENT,
            keyword=settings.SCORE_WEIGHT_KEYWORD,
        )

    if baseline_mode:
        weights = FusionWeights(tfidf=1.0, word_order=0.0, intent=0.0, keyword=0.0)

    # ── Step 1: Preprocess ────────────────────────────────────────────────────
    prep = preprocess(query)
    tokens = prep["filtered_tokens"]
    lemmas = prep["lemmas"]
    pos_tags = prep["pos_tags"]

    # ── Step 2: WordNet Expansion ─────────────────────────────────────────────
    expanded_lemmas = expand_with_wordnet(lemmas)
    expanded_query = " ".join(expanded_lemmas)

    # ── Step 3: Intent Classification ────────────────────────────────────────
    intent_result = classify_intent(query, lemmas)
    intent = intent_result["intent"]
    intent_score = intent_result["score"]

    # ── Step 4: TF-IDF Retrieval ──────────────────────────────────────────────
    # Use expanded query for better coverage
    candidates_raw = get_candidates(expanded_query, top_k=top_k)

    # ── Step 5: Score Fusion per Candidate ───────────────────────────────────
    fused_candidates = []
    for cand in candidates_raw:
        entry = cand["entry"]
        scores = fuse_scores(
            query_tokens=lemmas,
            entry=entry,
            tfidf_score=cand["tfidf_score"],
            detected_intent=intent,
            weights=weights,
        )
        fused_candidates.append({**cand, **scores})

    # Sort by final_score
    fused_candidates.sort(key=lambda x: x["final_score"], reverse=True)

    # ── Step 6: Domain Detection ──────────────────────────────────────────────
    max_tfidf = fused_candidates[0]["tfidf_score"] if fused_candidates else 0.0
    query_type = detect_query_type(
        query=query,
        lemmas=lemmas,
        max_tfidf_score=max_tfidf,
        confidence_threshold=settings.NLP_CONFIDENCE_THRESHOLD,
        ood_threshold=settings.OOD_CONFIDENCE_THRESHOLD,
    )

    # ── Step 7: Response Selection ────────────────────────────────────────────
    best = fused_candidates[0] if fused_candidates else None
    final_score = best["final_score"] if best else 0.0
    confidence = final_score  # primary confidence signal

    if query_type == "OUT_OF_DOMAIN":
        response = (
            f"I'm {COLLEGE_NAME}'s virtual assistant and I can only help with "
            "college-related questions such as admissions, schedule, fees, events, "
            "faculty, and facilities. Please ask me something related to the college!"
        )
        kb_entry_id = None
        selected_entry = None
    elif query_type == "UNKNOWN_INSTITUTIONAL" or confidence < settings.NLP_CONFIDENCE_THRESHOLD:
        response = (
            "I'm sorry, I don't have specific information about that in my knowledge base yet. "
            "Your query has been flagged for review, and our team will update the information soon. "
            "For urgent queries, please contact the college office directly."
        )
        kb_entry_id = None
        selected_entry = None
        query_type = "UNKNOWN_INSTITUTIONAL"
    else:
        selected_entry = best["entry"]
        response = selected_entry["answer"]
        kb_entry_id = selected_entry.get("id")
        # Append source if available
        src_title = selected_entry.get("source_title")
        src_url = selected_entry.get("source_url")
        if src_title or src_url:
            source_note = "\n\n*Source: "
            if src_title:
                source_note += src_title
            if src_url:
                source_note += f" — {src_url}"
            source_note += "*"
            response += source_note

    t_end = time.perf_counter()
    processing_time_ms = int((t_end - t_start) * 1000)

    # ── Debug Trace (for NLP Inspector) ──────────────────────────────────────
    debug = {
        "original_query": query,
        "normalized_query": prep["normalized"],
        "tokens": prep["tokens"],
        "filtered_tokens": tokens,
        "lemmas": lemmas,
        "pos_tags": pos_tags,
        "wordnet_expanded": expanded_lemmas,
        "intent": intent,
        "intent_score": round(intent_score, 4),
        "intent_method": intent_result.get("method"),
        "query_type": query_type,
        "weights_used": {
            "alpha_tfidf": round(weights.tfidf, 3),
            "beta_word_order": round(weights.word_order, 3),
            "gamma_intent": round(weights.intent, 3),
            "delta_keyword": round(weights.keyword, 3),
        },
        "top_candidates": [
            {
                "rank": i + 1,
                "id": str(c["entry"].get("id", "")),
                "question": c["entry"].get("question", ""),
                "category": c["entry"].get("category", ""),
                "tfidf_score": c["tfidf_score"],
                "word_order_score": c["word_order_score"],
                "intent_score": c["intent_score"],
                "keyword_score": c["keyword_score"],
                "final_score": c["final_score"],
            }
            for i, c in enumerate(fused_candidates[:top_k])
        ],
        "selected_kb_id": str(kb_entry_id) if kb_entry_id else None,
        "processing_time_ms": processing_time_ms,
        "baseline_mode": baseline_mode,
    }

    return {
        "response": response,
        "intent": intent,
        "intent_score": round(intent_score, 4),
        "tfidf_score": round(fused_candidates[0]["tfidf_score"] if fused_candidates else 0.0, 4),
        "word_order_score": round(fused_candidates[0]["word_order_score"] if fused_candidates else 0.0, 4),
        "keyword_score": round(fused_candidates[0]["keyword_score"] if fused_candidates else 0.0, 4),
        "final_score": round(final_score, 4),
        "confidence": round(confidence, 4),
        "query_type": query_type,
        "kb_entry_id": str(kb_entry_id) if kb_entry_id else None,
        "processing_time_ms": processing_time_ms,
        "debug": debug,
    }
