"""
NLP Preprocessor
================
Implements the text normalization pipeline from the research paper:
  - Lowercasing + punctuation removal
  - NLTK word_tokenize
  - Stop-word removal
  - WordNet Lemmatization
  - POS tagging

Engineering decision: uses NLTK's averaged_perceptron_tagger for POS tags,
which are then mapped to WordNet POS constants for accurate lemmatization.
"""
from __future__ import annotations

import re
import string
from typing import Dict, List, Tuple

import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Ensure required NLTK data is available
for _pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "averaged_perceptron_tagger",
             "averaged_perceptron_tagger_eng", "omw-1.4"]:
    try:
        nltk.data.find(f"tokenizers/{_pkg}" if "punkt" in _pkg else
                       f"corpora/{_pkg}" if _pkg in ("stopwords", "wordnet", "omw-1.4") else
                       f"taggers/{_pkg}")
    except Exception:
        nltk.download(_pkg, quiet=True)

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words("english"))
# Keep question words — they help with intent
_keep_words = {"who", "what", "when", "where", "how", "why", "which"}
_stop_words -= _keep_words


def _get_wordnet_pos(treebank_tag: str) -> str:
    """Map Penn Treebank POS tags to WordNet POS constants."""
    if treebank_tag.startswith("J"):
        return wordnet.ADJ
    elif treebank_tag.startswith("V"):
        return wordnet.VERB
    elif treebank_tag.startswith("N"):
        return wordnet.NOUN
    elif treebank_tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN


def preprocess(text: str) -> Dict:
    """
    Full preprocessing pipeline.

    Returns a dict with keys:
      - original: str
      - normalized: str
      - tokens: List[str]
      - filtered_tokens: List[str]
      - lemmas: List[str]
      - pos_tags: List[Tuple[str, str]]
    """
    # 1. Normalize
    normalized = text.lower().strip()
    normalized = re.sub(r"[^\w\s']", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # 2. Tokenize
    tokens = word_tokenize(normalized)

    # 3. Remove stop words (keep question words)
    filtered_tokens = [t for t in tokens if t.isalpha() and t not in _stop_words]

    # 4. POS tagging
    pos_tags: List[Tuple[str, str]] = nltk.pos_tag(filtered_tokens)

    # 5. Lemmatize using POS-aware lemmatizer
    lemmas = [
        _lemmatizer.lemmatize(word, _get_wordnet_pos(tag))
        for word, tag in pos_tags
    ]

    return {
        "original": text,
        "normalized": normalized,
        "tokens": tokens,
        "filtered_tokens": filtered_tokens,
        "pos_tags": [(w, t) for w, t in pos_tags],
        "lemmas": lemmas,
    }
