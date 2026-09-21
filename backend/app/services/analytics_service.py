"""Analytics service — aggregated stats for admin dashboard."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Conversation, Feedback, KnowledgeEntry, Message, UnresolvedQuery, UnresolvedStatus, User
)
from app.nlp.retriever import is_index_ready, index_size


async def get_overview(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_convs = (await db.execute(select(func.count(Conversation.id)))).scalar_one()
    total_msgs = (await db.execute(
        select(func.count(Message.id)).where(Message.role == "assistant")
    )).scalar_one()
    total_kb = (await db.execute(
        select(func.count(KnowledgeEntry.id)).where(
            KnowledgeEntry.is_deleted == False, KnowledgeEntry.is_active == True
        )
    )).scalar_one()
    open_unresolved = (await db.execute(
        select(func.count(UnresolvedQuery.id)).where(
            UnresolvedQuery.status == UnresolvedStatus.OPEN
        )
    )).scalar_one()
    avg_rating = (await db.execute(select(func.avg(Feedback.rating)))).scalar_one()

    return {
        "total_users": total_users,
        "total_conversations": total_convs,
        "total_messages": total_msgs,
        "total_kb_entries": total_kb,
        "unresolved_open": open_unresolved,
        "avg_satisfaction": round(float(avg_rating), 2) if avg_rating else None,
        "index_ready": is_index_ready(),
        "index_size": index_size(),
    }


async def get_intent_distribution(db: AsyncSession) -> List[dict]:
    result = await db.execute(
        select(Message.intent, func.count(Message.id).label("count"))
        .where(Message.role == "assistant", Message.intent.isnot(None))
        .group_by(Message.intent)
        .order_by(func.count(Message.id).desc())
    )
    rows = result.all()
    total = sum(r.count for r in rows)
    return [
        {
            "intent": r.intent,
            "count": r.count,
            "percentage": round(r.count / total * 100, 1) if total > 0 else 0.0,
        }
        for r in rows
    ]


async def get_daily_stats(db: AsyncSession, days: int = 30) -> List[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("total"),
            func.sum(
                func.cast(Message.query_type == "ANSWERED", func.Integer())
            ).label("answered"),
        )
        .where(Message.role == "assistant", Message.created_at >= cutoff)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at).asc())
    )
    rows = result.all()
    return [
        {
            "date": str(r.date),
            "total": r.total,
            "answered": r.answered or 0,
            "unresolved": r.total - (r.answered or 0),
        }
        for r in rows
    ]


async def get_feedback_stats(db: AsyncSession) -> dict:
    avg_rating = (await db.execute(select(func.avg(Feedback.rating)))).scalar_one()
    total = (await db.execute(select(func.count(Feedback.id)))).scalar_one()

    dist_result = await db.execute(
        select(Feedback.rating, func.count(Feedback.id).label("count"))
        .group_by(Feedback.rating)
        .order_by(Feedback.rating)
    )
    dist = {str(r.rating): r.count for r in dist_result.all()}

    return {
        "avg_rating": round(float(avg_rating), 2) if avg_rating else None,
        "total_feedback": total,
        "rating_distribution": dist,
    }
