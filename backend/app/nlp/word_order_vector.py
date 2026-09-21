"""
Word Order Vector (WOV) Similarity
====================================
Implements the Word Order Vector similarity measure as described in the
research paper "AI Chatbot for Smart Communities".

The Word Order Vector represents each sentence as a vector in word-space,
where the position of each word encodes its order in the sentence.
Similarity is based on how closely word orders match between query and KB entry.

Reference:
  Li, Y. et al. (2006). Sentence Similarity Based on Semantic Nets and Corpus Statistics.
  IEEE TKDE 18(8):1138–1150.

Engineering note: we use a simplified but faithful implementation that:
  1. Builds a joint vocabulary from both sentences
  2. Encodes word order as index+1 (0 for absent words)
  3. Computes similarity as 1 - norm(r1-r2) / norm(r1+r2)
"""
from __future__ import annotations

from typing import List

import numpy as np


def _build_order_vector(tokens: List[str], vocab: List[str]) -> np.ndarray:
    """
    For each word in vocab, the vector value is:
      - The 1-based position of the word in 'tokens' if present
      - 0 if absent
    """
    vec = np.zeros(len(vocab))
    for i, word in enumerate(vocab):
        if word in tokens:
            idx = tokens.index(word)
            vec[i] = idx + 1  # 1-based
    return vec


def word_order_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Computes WOV similarity between two token sequences.
    Returns a float in [0, 1].
    """
    if not tokens1 or not tokens2:
        return 0.0

    # Joint vocabulary (unique words from both sentences, ordered)
    vocab = list(dict.fromkeys(tokens1 + tokens2))

    r1 = _build_order_vector(tokens1, vocab)
    r2 = _build_order_vector(tokens2, vocab)

    diff_norm = np.linalg.norm(r1 - r2)
    sum_norm = np.linalg.norm(r1 + r2)

    if sum_norm == 0:
        return 1.0

    return float(1.0 - diff_norm / sum_norm)
