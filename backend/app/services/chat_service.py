"""
Chat service — orchestrates NLP pipeline, persists messages and conversations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Conversation, Message, NlpSettings, UnresolvedQuery, UnresolvedStatus
from app.nlp.pipeline import run_pipeline
from app.nlp.score_fusion import FusionWeights

logger = get_logger(__name__)


async def _get_fusion_weights(db: AsyncSession) -> FusionWeights:
    """Load current score fusion weights from DB."""
    result = await db.execute(select(NlpSettings))
    rows = result.scalars().all()
    w = {r.name: r.value for r in rows}
    return FusionWeights(
        tfidf=w.get("alpha_tfidf", settings.SCORE_WEIGHT_TFIDF),
        word_order=w.get("beta_word_order", settings.SCORE_WEIGHT_WORD_ORDER),
        intent=w.get("gamma_intent", settings.SCORE_WEIGHT_INTENT),
        keyword=w.get("delta_keyword", settings.SCORE_WEIGHT_KEYWORD),
    )


async def get_or_create_conversation(
    db: AsyncSession, user_id: str, session_id: Optional[str]
) -> Conversation:
    if session_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(session_id),
                Conversation.user_id == uuid.UUID(user_id),
            )
        )
        conv = result.scalars().first()
        if conv:
            return conv

    conv = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        started_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    await db.flush()
    return conv


async def process_message(
    db: AsyncSession,
    user_id: str,
    session_id: Optional[str],
    query: str,
    baseline_mode: bool = False,
) -> dict:
    """Run the NLP pipeline, persist the exchange, and return the full result."""
    # Load fusion weights from DB
    weights = await _get_fusion_weights(db)

    # Run NLP pipeline
    result = run_pipeline(
        query=query,
        weights=weights,
        baseline_mode=baseline_mode,
    )

    # Get/create conversation
    conv = await get_or_create_conversation(db, user_id, session_id)

    # Update conversation title from first user message
    if not conv.title:
        conv.title = query[:60] + ("..." if len(query) > 60 else "")

    # Persist user message
    user_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="user",
        content=query,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)

    # Persist assistant message
    asst_msg = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="assistant",
        content=result["response"],
        intent=result["intent"],
        intent_score=result["intent_score"],
        tfidf_score=result["tfidf_score"],
        word_order_score=result["word_order_score"],
        keyword_score=result["keyword_score"],
        final_score=result["final_score"],
        confidence=result["confidence"],
        query_type=result["query_type"],
        processing_time_ms=result["processing_time_ms"],
        kb_entry_id=uuid.UUID(result["kb_entry_id"]) if result.get("kb_entry_id") else None,
        nlp_debug_json=result["debug"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(asst_msg)
    await db.flush()

    # Create unresolved query if needed
    if result["query_type"] == "UNKNOWN_INSTITUTIONAL":
        uq = UnresolvedQuery(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            message_id=asst_msg.id,
            query=query,
            intent=result["intent"],
            confidence=result["confidence"],
            reason="Below confidence threshold",
            status=UnresolvedStatus.OPEN,
        )
        db.add(uq)

    return {
        "message_id": str(asst_msg.id),
        "session_id": str(conv.id),
        **result,
    }


async def get_user_conversations(
    db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
) -> List[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == uuid.UUID(user_id))
        .order_by(Conversation.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


async def get_conversation_messages(
    db: AsyncSession, conversation_id: str, user_id: str
) -> List[Message]:
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.id == uuid.UUID(conversation_id),
            Conversation.user_id == uuid.UUID(user_id),
        )
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()
