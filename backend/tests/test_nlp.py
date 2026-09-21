"""Tests for NLP pipeline components."""
import pytest
from app.nlp.preprocessor import preprocess
from app.nlp.wordnet_expander import expand_with_wordnet
from app.nlp.intent_classifier import classify_intent
from app.nlp.word_order_vector import word_order_similarity
from app.nlp.score_fusion import FusionWeights, fuse_scores
from app.nlp.domain_detector import detect_query_type


def test_preprocessor_basic():
    result = preprocess("What are the admission requirements?")
    assert "tokens" in result
    assert "lemmas" in result
    assert "pos_tags" in result
    assert len(result["lemmas"]) > 0


def test_preprocessor_normalizes():
    result = preprocess("WHAT is the FEE structure!!!")
    assert result["normalized"] == result["normalized"].lower()


def test_wordnet_expansion():
    expanded = expand_with_wordnet(["student", "admission"])
    assert len(expanded) >= 2


def test_intent_admissions():
    result = classify_intent("How do I apply for admission?", ["apply", "admission"])
    assert result["intent"] == "admissions"
    assert result["score"] > 0.5


def test_intent_staff():
    result = classify_intent("Who is the HOD of CSE?", ["hod", "cse"])
    assert result["intent"] == "staff"


def test_intent_fees():
    result = classify_intent("What is the fee structure?", ["fee", "structure"])
    assert result["intent"] == "fees"


def test_intent_exam():
    result = classify_intent("When is the exam timetable?", ["exam", "timetable"])
    assert result["intent"] == "exam"


def test_intent_schedule():
    result = classify_intent("When does the semester begin?", ["semester", "begin"])
    assert result["intent"] == "schedule"


def test_word_order_identical():
    score = word_order_similarity(["hello", "world"], ["hello", "world"])
    assert score == 1.0


def test_word_order_reversed():
    score = word_order_similarity(["hello", "world"], ["world", "hello"])
    assert 0.0 <= score < 1.0


def test_word_order_empty():
    score = word_order_similarity([], ["hello"])
    assert score == 0.0


def test_score_fusion_weights():
    w = FusionWeights(tfidf=0.5, word_order=0.3, intent=0.2, keyword=0.0)
    normalized = w.normalized()
    total = normalized.tfidf + normalized.word_order + normalized.intent + normalized.keyword
    assert abs(total - 1.0) < 0.001


def test_fuse_scores():
    entry = {"category": "fees", "question": "fee structure", "keywords": ["fee", "tuition"]}
    scores = fuse_scores(
        query_tokens=["fee", "structure"],
        entry=entry,
        tfidf_score=0.7,
        detected_intent="fees",
        weights=FusionWeights(),
    )
    assert "final_score" in scores
    assert 0.0 <= scores["final_score"] <= 1.0
    assert scores["intent_score"] == 1.0  # intent matches category


def test_domain_detector_ood():
    result = detect_query_type(
        query="what is the weather today",
        lemmas=["weather", "today"],
        max_tfidf_score=0.01,
        confidence_threshold=0.35,
        ood_threshold=0.10,
    )
    assert result == "OUT_OF_DOMAIN"


def test_domain_detector_unknown_institutional():
    result = detect_query_type(
        query="what is the college parking policy",
        lemmas=["college", "parking", "policy"],
        max_tfidf_score=0.05,
        confidence_threshold=0.35,
        ood_threshold=0.10,
    )
    assert result == "UNKNOWN_INSTITUTIONAL"
