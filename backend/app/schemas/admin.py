"""Analytics and admin schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class OverviewStats(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    total_kb_entries: int
    unresolved_open: int
    avg_satisfaction: Optional[float]
    index_ready: bool
    index_size: int


class IntentStat(BaseModel):
    intent: str
    count: int
    percentage: float


class DailyStat(BaseModel):
    date: str
    total: int
    answered: int
    unresolved: int


class FeedbackStats(BaseModel):
    avg_rating: Optional[float]
    total_feedback: int
    rating_distribution: Dict[str, int]


class AdminUserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class NlpSettingsOut(BaseModel):
    alpha_tfidf: float
    beta_word_order: float
    gamma_intent: float
    delta_keyword: float
    confidence_threshold: float
    ood_threshold: float


class NlpSettingsUpdate(BaseModel):
    alpha_tfidf: Optional[float] = None
    beta_word_order: Optional[float] = None
    gamma_intent: Optional[float] = None
    delta_keyword: Optional[float] = None
    confidence_threshold: Optional[float] = None
    ood_threshold: Optional[float] = None


class SystemStatusOut(BaseModel):
    status: str
    database: str
    nlp_index: str
    index_size: int
    uptime_seconds: Optional[float]
    version: str
