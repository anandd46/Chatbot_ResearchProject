"""
SQLAlchemy ORM models — complete schema for all 14 tables.
Uses declarative_base with typed columns (SQLAlchemy 2.x style).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
    Uuid,
    JSON,
    UniqueConstraint,
    func,
)

# Dummy ARRAY for SQLite compatibility
class ARRAY(JSON):
    def __init__(self, item_type=None, **kwargs):
        super().__init__(**kwargs)

UUID = Uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Base ─────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Enums ────────────────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class UnresolvedStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class QueryType(str, enum.Enum):
    ANSWERED = "ANSWERED"
    UNKNOWN_INSTITUTIONAL = "UNKNOWN_INSTITUTIONAL"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


class SourceType(str, enum.Enum):
    official_website = "official_website"
    brochure = "brochure"
    notice_board = "notice_board"
    staff_input = "staff_input"
    handbook = "handbook"
    other = "other"


class EvalMode(str, enum.Enum):
    baseline = "baseline"
    enhanced = "enhanced"


# ── Users ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(20), nullable=False, default=UserRole.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now()
    )

    # Relationships
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user")
    feedback: Mapped[List["Feedback"]] = relationship(back_populates="user")
    unresolved_queries: Mapped[List["UnresolvedQuery"]] = relationship(
        back_populates="user", foreign_keys="UnresolvedQuery.user_id"
    )


# ── Refresh Tokens ───────────────────────────────────────────────────────────
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


# ── Knowledge Entries ────────────────────────────────────────────────────────
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    # Source traceability
    source_title: Mapped[Optional[str]] = mapped_column(String(255))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # soft delete
    version_count: Mapped[int] = mapped_column(Integer, default=1)
    # Cached NLP data (serialized JSON)
    tfidf_vector_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    # Audit
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now()
    )

    versions: Mapped[List["KnowledgeVersion"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


# ── Knowledge Versions ───────────────────────────────────────────────────────
class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_entries.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    entry: Mapped["KnowledgeEntry"] = relationship(back_populates="versions")


# ── Conversations ────────────────────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


# ── Messages ─────────────────────────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # NLP metadata (only for assistant messages)
    intent: Mapped[Optional[str]] = mapped_column(String(100))
    intent_score: Mapped[Optional[float]] = mapped_column(Float)
    tfidf_score: Mapped[Optional[float]] = mapped_column(Float)
    word_order_score: Mapped[Optional[float]] = mapped_column(Float)
    keyword_score: Mapped[Optional[float]] = mapped_column(Float)
    final_score: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    query_type: Mapped[Optional[str]] = mapped_column(String(30))
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    kb_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    nlp_debug_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    feedback: Mapped[Optional["Feedback"]] = relationship(back_populates="message", uselist=False)
    unresolved_query: Mapped[Optional["UnresolvedQuery"]] = relationship(
        back_populates="message", uselist=False
    )


# ── Feedback ─────────────────────────────────────────────────────────────────
class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    message: Mapped["Message"] = relationship(back_populates="feedback")
    user: Mapped["User"] = relationship(back_populates="feedback")


# ── Unresolved Queries ───────────────────────────────────────────────────────
class UnresolvedQuery(Base):
    __tablename__ = "unresolved_queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL")
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[UnresolvedStatus] = mapped_column(
        String(20), default=UnresolvedStatus.OPEN, nullable=False
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    kb_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), comment="Set when converted to a KB entry"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="unresolved_queries", foreign_keys=[user_id])
    message: Mapped[Optional["Message"]] = relationship(back_populates="unresolved_query")


# ── Audit Logs ───────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(100))
    target_id: Mapped[Optional[str]] = mapped_column(String(255))
    detail: Mapped[Optional[Dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


# ── NLP Settings (Score Fusion Weights) ─────────────────────────────────────
class NlpSettings(Base):
    __tablename__ = "nlp_settings"
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


# ── System Settings (Key-Value) ──────────────────────────────────────────────
class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


# ── Evaluation Datasets ──────────────────────────────────────────────────────
class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cases: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    runs: Mapped[List["EvaluationRun"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


# ── Evaluation Runs ──────────────────────────────────────────────────────────
class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_datasets.id", ondelete="CASCADE"))
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # baseline | enhanced
    weights_snapshot: Mapped[Optional[Dict]] = mapped_column(JSON)
    # Aggregate metrics (computed after run)
    intent_accuracy: Mapped[Optional[float]] = mapped_column(Float)
    retrieval_success_rate: Mapped[Optional[float]] = mapped_column(Float)
    unknown_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_processing_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    run_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    dataset: Mapped["EvaluationDataset"] = relationship(back_populates="runs")
    results: Mapped[List["EvaluationResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


# ── Evaluation Results (per case) ────────────────────────────────────────────
class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True
    )
    case_index: Mapped[int] = mapped_column(Integer, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[Optional[str]] = mapped_column(String(100))
    expected_kb_entry_id: Mapped[Optional[str]] = mapped_column(String(255))
    predicted_intent: Mapped[Optional[str]] = mapped_column(String(100))
    predicted_kb_entry_id: Mapped[Optional[str]] = mapped_column(String(255))
    intent_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    retrieval_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    final_score: Mapped[Optional[float]] = mapped_column(Float)
    query_type: Mapped[Optional[str]] = mapped_column(String(30))
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    debug_json: Mapped[Optional[Dict]] = mapped_column(JSON)

    run: Mapped["EvaluationRun"] = relationship(back_populates="results")
