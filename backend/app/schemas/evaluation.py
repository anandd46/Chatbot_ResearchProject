"""Evaluation schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class EvalCase(BaseModel):
    query: str
    expected_intent: Optional[str] = None
    expected_category: Optional[str] = None


class EvalDatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cases: List[EvalCase]


class EvalDatasetOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    case_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RunEvalRequest(BaseModel):
    mode: str = "enhanced"  # baseline | enhanced


class EvalResultItem(BaseModel):
    case_index: int
    query: str
    expected_intent: Optional[str]
    predicted_intent: Optional[str]
    intent_correct: Optional[bool]
    retrieval_correct: Optional[bool]
    final_score: Optional[float]
    query_type: Optional[str]
    processing_time_ms: Optional[int]


class EvalRunOut(BaseModel):
    id: str
    dataset_id: str
    mode: str
    weights_snapshot: Optional[Dict]
    intent_accuracy: Optional[float]
    retrieval_success_rate: Optional[float]
    unknown_rate: Optional[float]
    avg_processing_time_ms: Optional[float]
    total_cases: int
    run_at: datetime
    results: Optional[List[EvalResultItem]] = None

    class Config:
        from_attributes = True


class ComparisonReport(BaseModel):
    baseline_run: EvalRunOut
    enhanced_run: EvalRunOut
    intent_accuracy_delta: float
    retrieval_success_delta: float
    unknown_rate_delta: float
    avg_time_delta: float
    winner: str  # "baseline" | "enhanced" | "tie"
