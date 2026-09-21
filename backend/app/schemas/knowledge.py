"""Knowledge base schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeEntryCreate(BaseModel):
    category: str
    question: str
    answer: str
    keywords: List[str] = []
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    last_verified: Optional[datetime] = None
    reason: Optional[str] = None  # For version log


class KnowledgeEntryUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    last_verified: Optional[datetime] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = None


class KnowledgeEntryOut(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    keywords: List[str]
    source_title: Optional[str]
    source_url: Optional[str]
    source_type: Optional[str]
    last_verified: Optional[datetime]
    is_active: bool
    is_deleted: bool
    version_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeVersionOut(BaseModel):
    id: str
    version: int
    question: str
    answer: str
    keywords: List[str]
    changed_by: Optional[str]
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ImportPreview(BaseModel):
    total: int
    valid: int
    invalid: int
    errors: List[str]
    preview_rows: List[dict]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
