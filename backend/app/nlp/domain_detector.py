"""
Out-of-Domain Detector
=======================
Distinguishes between two failure modes:

  UNKNOWN_INSTITUTIONAL_QUERY
    The user is asking about the college but the KB has no answer.
    → Should be flagged for admin review and KB expansion.

  OUT_OF_DOMAIN_QUERY
    The user is asking about something completely unrelated to the institution.
    → Should be politely declined; not flagged as a gap in the KB.

Engineering decision: we use a dual-threshold approach:
  - If TF-IDF max score < OOD threshold AND no institutional keywords → OUT_OF_DOMAIN
  - If TF-IDF max score < confidence threshold BUT institutional keywords present → UNKNOWN_INSTITUTIONAL
"""
from __future__ import annotations

import re

INSTITUTIONAL_KEYWORDS = {
    "college", "department", "faculty", "student", "course", "semester",
    "exam", "fee", "hostel", "library", "admission", "campus", "class",
    "lecture", "professor", "hod", "principal", "dean", "institute", "university",
    "schedule", "timetable", "lab", "result", "marks", "grade", "club",
    "event", "fest", "canteen", "placement", "internship", "project",
    "thesis", "research", "sports", "scholarship", "syllabus", "curriculum",
}

INSTITUTIONAL_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(INSTITUTIONAL_KEYWORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

CLEAR_OOD_INDICATORS = {
    "weather", "cricket", "football", "movie", "film", "recipe", "cooking",
    "stock", "crypto", "bitcoin", "politics", "news", "celebrity", "gossip",
    "astrology", "horoscope", "joke", "meme", "song", "music", "game",
}


def detect_query_type(
    query: str,
    lemmas: list,
    max_tfidf_score: float,
    confidence_threshold: float,
    ood_threshold: float,
) -> str:
    """
    Returns: 'ANSWERED' | 'UNKNOWN_INSTITUTIONAL' | 'OUT_OF_DOMAIN'

    Note: 'ANSWERED' here just means "not OOD" — the retriever decides
    whether confidence is high enough to return an answer.
    """
    query_lower = query.lower()
    all_words = set(lemmas) | set(query_lower.split())

    # Clear OOD indicator
    has_ood = bool(all_words & CLEAR_OOD_INDICATORS)
    has_institutional = bool(INSTITUTIONAL_PATTERN.search(query_lower))

    if has_ood and not has_institutional:
        return "OUT_OF_DOMAIN"

    if max_tfidf_score < ood_threshold and not has_institutional:
        return "OUT_OF_DOMAIN"

    # Institutional context exists but below confidence threshold
    if max_tfidf_score < confidence_threshold:
        return "UNKNOWN_INSTITUTIONAL"

    return "ANSWERED"
