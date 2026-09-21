"""Chat schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class NlpDebug(BaseModel):
    original_query: str
    normalized_query: str
    tokens: List[str]
    filtered_tokens: List[str]
    lemmas: List[str]
    pos_tags: List[List[str]]
    wordnet_expanded: List[str]
    intent: str
    intent_score: float
    intent_method: Optional[str]
    query_type: str
    weights_used: Dict[str, float]
    top_candidates: List[Dict[str, Any]]
    selected_kb_id: Optional[str]
    processing_time_ms: int
    baseline_mode: bool


class ChatResponse(BaseModel):
    message_id: str
    session_id: str
    response: str
    intent: str
    intent_score: float
    tfidf_score: float
    word_order_score: float
    keyword_score: float
    final_score: float
    confidence: float
    query_type: str
    kb_entry_id: Optional[str]
    processing_time_ms: int
    debug: Optional[NlpDebug] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    intent: Optional[str]
    confidence: Optional[float]
    query_type: Optional[str]
    processing_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    title: Optional[str]
    started_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True
