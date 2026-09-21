"""Unresolved query schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UnresolvedQueryOut(BaseModel):
    id: str
    user_id: Optional[str]
    message_id: Optional[str]
    query: str
    intent: Optional[str]
    confidence: Optional[float]
    reason: Optional[str]
    status: str
    admin_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    kb_entry_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UnresolvedQueryUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None


class ConvertToKbRequest(BaseModel):
    category: str
    question: str
    answer: str
    keywords: list = []
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
