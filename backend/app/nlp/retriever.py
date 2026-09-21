"""
TF-IDF Retriever
================
Builds and maintains a TF-IDF index over all active knowledge base entries.
Provides cosine-similarity-based retrieval.

Engineering decisions:
  - Index is built in-memory at startup and on every KB update/import.
  - Uses sklearn TfidfVectorizer with character n-grams enabled (ngram_range=(1,2))
    for better partial-match coverage.
  - Thread-safe index rebuilding via a module-level lock.
  - The retriever exposes an abstraction layer: get_candidates() returns
    ranked candidates; future implementations can swap the inner logic
    (e.g., sentence-transformers, OpenAI embeddings) without changing callers.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.logging import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()

# Index state
_vectorizer: Optional[TfidfVectorizer] = None
_matrix = None  # scipy sparse matrix
_entries: List[Dict[str, Any]] = []  # [{id, question, answer, keywords, category, ...}]


def build_index(knowledge_entries: List[Dict[str, Any]]) -> None:
    """
    (Re)build TF-IDF index from a list of knowledge entry dicts.
    Each dict must have: id, question, answer, keywords (list), category.
    Thread-safe.
    """
    global _vectorizer, _matrix, _entries

    if not knowledge_entries:
        logger.warning("build_index called with empty knowledge base")
        with _lock:
            _entries = []
            _vectorizer = None
            _matrix = None
        return

    # Build combined text: question + keywords for each entry
    corpus = []
    for entry in knowledge_entries:
        kw = " ".join(entry.get("keywords") or [])
        text = f"{entry['question']} {kw}"
        corpus.append(text)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        analyzer="word",
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(corpus)

    with _lock:
        _vectorizer = vectorizer
        _matrix = matrix
        _entries = list(knowledge_entries)

    logger.info(f"TF-IDF index built: {len(knowledge_entries)} entries")


def get_tfidf_scores(query_text: str) -> List[float]:
    """Return per-entry TF-IDF cosine similarity scores for a query."""
    with _lock:
        if _vectorizer is None or _matrix is None or not _entries:
            return []
        try:
            query_vec = _vectorizer.transform([query_text])
            scores = cosine_similarity(query_vec, _matrix)[0]
            return scores.tolist()
        except Exception as e:
            logger.error(f"TF-IDF scoring error: {e}")
            return []


def get_candidates(
    query_text: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Return top-k knowledge entries by TF-IDF score.
    Each result has: entry (dict), tfidf_score (float).
    """
    scores = get_tfidf_scores(query_text)
    if not scores:
        return []

    scored = sorted(
        enumerate(scores), key=lambda x: x[1], reverse=True
    )[:top_k]

    results = []
    for idx, score in scored:
        if score > 0:
            results.append({"entry": _entries[idx], "tfidf_score": float(score)})
    return results


def is_index_ready() -> bool:
    return _vectorizer is not None and _matrix is not None and len(_entries) > 0


def index_size() -> int:
    return len(_entries)
