"""
Intent Classifier
=================
Classifies user queries into one of 12 institutional intents using:
  1. Regex/keyword pattern matching (fast, deterministic)
  2. TF-IDF cosine similarity over intent exemplar corpus (fallback)

Intents:
  admissions, schedule, events, staff, fees, library, hostel,
  exam, facilities, contact, general, unknown

Engineering decision: pattern matching takes precedence over TF-IDF
when confidence is high. This keeps the system interpretable.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ── Intent Definitions ────────────────────────────────────────────────────────
INTENT_PATTERNS: Dict[str, List[str]] = {
    "admissions": [
        r"\b(admiss|apply|application|eligibil|enroll|admission|joining|how to join|"
        r"required document|qualification|merit|entrance|cutoff|seat)\b"
    ],
    "schedule": [
        r"\b(schedule|timetable|time table|semester|term|date|when does|academic calendar|"
        r"holiday|vacation|break|class timing|lecture|start date|end date)\b"
    ],
    "events": [
        r"\b(event|fest|festival|cultural|annual day|seminar|workshop|competition|"
        r"happening|program|activity|celebration|techfest)\b"
    ],
    "staff": [
        r"\b(hod|head of department|professor|faculty|lecturer|teacher|staff|"
        r"who is|principal|dean|coordinator|contact person)\b"
    ],
    "fees": [
        r"\b(fee|fees|tuition|cost|payment|scholarship|stipend|financial|charge|"
        r"how much|price|amount|installment|hostel fee|annual fee)\b"
    ],
    "library": [
        r"\b(library|book|journal|e-resource|reading room|issue|return|catalog|"
        r"digital library|library timing|borrow)\b"
    ],
    "hostel": [
        r"\b(hostel|accommodation|dorm|dormitory|room|warden|mess|canteen|residential|"
        r"stay|boarding|pg|paying guest)\b"
    ],
    "exam": [
        r"\b(exam|examination|test|quiz|internal|external|practical|viva|result|"
        r"mark|grade|cgpa|sgpa|transcript|hall ticket|admit card)\b"
    ],
    "facilities": [
        r"\b(facilit|lab|laboratory|sports|gym|wifi|internet|transport|bus|parking|"
        r"playground|infrastructure|computer center|medical|clinic)\b"
    ],
    "contact": [
        r"\b(contact|phone|email|address|location|office|helpline|number|reach|"
        r"timing|open|close|working hour|visiting hour)\b"
    ],
    "general": [
        r"\b(college|institute|university|about|history|establish|affiliated|"
        r"naac|accreditation|vision|mission|overview|rank|ranking)\b"
    ],
}

INTENT_EXEMPLARS: Dict[str, List[str]] = {
    "admissions": [
        "how do I apply for admission",
        "what are the admission requirements",
        "eligibility criteria for BTech",
        "documents needed for enrollment",
        "admission process for MCA",
        "merit based admission",
        "application form for new students",
    ],
    "schedule": [
        "when does the new semester start",
        "academic calendar for this year",
        "class timetable",
        "semester end date",
        "holiday list",
        "lecture schedule",
    ],
    "events": [
        "upcoming college events",
        "annual cultural fest",
        "technical seminar this month",
        "student competition",
        "what events are happening",
    ],
    "staff": [
        "who is the HOD of computer science",
        "contact details of the principal",
        "faculty list for electronics",
        "who is the dean of academics",
    ],
    "fees": [
        "what is the fee structure",
        "how much is the tuition fee",
        "scholarship available",
        "fee payment procedure",
    ],
    "library": [
        "library working hours",
        "how to borrow books",
        "e-journals access",
        "library book return",
    ],
    "hostel": [
        "hostel facilities",
        "how to apply for hostel",
        "hostel fee per semester",
        "mess menu",
    ],
    "exam": [
        "exam timetable release",
        "internal exam schedule",
        "how to check results",
        "hall ticket download",
        "CGPA calculation",
    ],
    "facilities": [
        "computer lab facilities",
        "sports facilities on campus",
        "campus wifi availability",
        "college transport facility",
    ],
    "contact": [
        "college phone number",
        "office hours",
        "how to contact admission office",
        "email address of registrar",
    ],
    "general": [
        "about the college",
        "when was the college established",
        "NAAC accreditation status",
        "college vision and mission",
    ],
}

# Build TF-IDF model over exemplars at import time
_all_exemplars: List[str] = []
_exemplar_intents: List[str] = []
for intent, examples in INTENT_EXEMPLARS.items():
    for ex in examples:
        _all_exemplars.append(ex)
        _exemplar_intents.append(intent)

_tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
_exemplar_matrix = _tfidf_vectorizer.fit_transform(_all_exemplars)


def classify_intent(query: str, lemmas: List[str]) -> Dict:
    """
    Returns:
      intent: str
      score: float (0–1)
      method: 'pattern' | 'tfidf'
    """
    query_lower = query.lower()
    joined_lemmas = " ".join(lemmas)

    # 1. Pattern matching
    best_pattern_intent = None
    best_pattern_count = 0
    for intent, patterns in INTENT_PATTERNS.items():
        count = 0
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                count += 1
        if count > best_pattern_count:
            best_pattern_count = count
            best_pattern_intent = intent

    if best_pattern_intent and best_pattern_count >= 1:
        # Pattern confidence proportional to match count
        score = min(0.95, 0.65 + best_pattern_count * 0.10)
        return {"intent": best_pattern_intent, "score": score, "method": "pattern"}

    # 2. TF-IDF cosine similarity over exemplars
    try:
        query_vec = _tfidf_vectorizer.transform([query_lower + " " + joined_lemmas])
        similarities = cosine_similarity(query_vec, _exemplar_matrix)[0]
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score > 0.1:
            return {
                "intent": _exemplar_intents[best_idx],
                "score": best_score,
                "method": "tfidf",
            }
    except Exception:
        pass

    return {"intent": "unknown", "score": 0.0, "method": "fallback"}
