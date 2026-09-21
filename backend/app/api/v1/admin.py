"""Admin routes — analytics, users, NLP inspector, settings, conversations."""


import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, get_current_user
from app.db.models import Conversation, Message, NlpSettings, User
from app.db.session import get_db
from app.nlp.pipeline import run_pipeline
from app.nlp.score_fusion import FusionWeights
from app.schemas.admin import (
    AdminUserOut, FeedbackStats, NlpSettingsOut, NlpSettingsUpdate,
    OverviewStats, SystemStatusOut
)
from app.services import analytics_service

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Analytics ────────────────────────────────────────────────────────────────
@router.get("/analytics/overview", response_model=OverviewStats)
async def overview(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    return await analytics_service.get_overview(db)


@router.get("/analytics/intents")
async def intent_distribution(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    return await analytics_service.get_intent_distribution(db)


@router.get("/analytics/daily")
async def daily_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    return await analytics_service.get_daily_stats(db, days)


@router.get("/analytics/feedback", response_model=FeedbackStats)
async def feedback_stats(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    return await analytics_service.get_feedback_stats(db)


# ── Users ─────────────────────────────────────────────────────────────────────
@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
    page: int = 1,
    page_size: int = 20,
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()
    return [AdminUserOut.model_validate(u) for u in users]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "role" in body:
        user.role = body["role"]
    if "is_active" in body:
        user.is_active = body["is_active"]
    return {"message": "User updated"}


# ── Conversations ─────────────────────────────────────────────────────────────
@router.get("/conversations")
async def list_all_conversations(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
    page: int = 1,
    page_size: int = 20,
):
    result = await db.execute(
        select(Conversation).order_by(Conversation.started_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    convs = result.scalars().all()
    return [{"id": str(c.id), "user_id": str(c.user_id), "title": c.title, "started_at": c.started_at} for c in convs]


@router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conv_id))
        .order_by(Message.created_at.asc())
    )
    msgs = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "confidence": m.confidence,
            "query_type": m.query_type,
            "final_score": m.final_score,
            "processing_time_ms": m.processing_time_ms,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


# ── NLP Inspector ─────────────────────────────────────────────────────────────
@router.post("/nlp/inspect")
async def nlp_inspect(body: dict, _=Depends(require_admin)):
    query = body.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    result = run_pipeline(query=query)
    return result["debug"]


# ── NLP Settings ──────────────────────────────────────────────────────────────
@router.get("/settings/nlp", response_model=NlpSettingsOut)
async def get_nlp_settings(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(NlpSettings))
    rows = result.scalars().all()
    w = {r.name: r.value for r in rows}
    return NlpSettingsOut(
        alpha_tfidf=w.get("alpha_tfidf", 0.40),
        beta_word_order=w.get("beta_word_order", 0.25),
        gamma_intent=w.get("gamma_intent", 0.20),
        delta_keyword=w.get("delta_keyword", 0.15),
        confidence_threshold=w.get("confidence_threshold", 0.35),
        ood_threshold=w.get("ood_threshold", 0.10),
    )


@router.patch("/settings/nlp", response_model=NlpSettingsOut)
async def update_nlp_settings(
    body: NlpSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    mapping = {
        "alpha_tfidf": body.alpha_tfidf,
        "beta_word_order": body.beta_word_order,
        "gamma_intent": body.gamma_intent,
        "delta_keyword": body.delta_keyword,
        "confidence_threshold": body.confidence_threshold,
        "ood_threshold": body.ood_threshold,
    }
    for name, value in mapping.items():
        if value is not None:
            result = await db.execute(select(NlpSettings).where(NlpSettings.name == name))
            row = result.scalars().first()
            if row:
                row.value = value
                row.updated_by = current_user.id

    return await get_nlp_settings(db)


# ── System Status ─────────────────────────────────────────────────────────────
@router.get("/status", response_model=SystemStatusOut)
async def system_status(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    from app.nlp.retriever import is_index_ready, index_size
    from app.core.config import settings as cfg

    # Check DB
    try:
        await db.execute(select(User).limit(1))
        db_status = "ok"
    except Exception:
        db_status = "error"

    from app.nlp.retriever import is_index_ready, index_size
    return SystemStatusOut(
        status="ok" if db_status == "ok" and is_index_ready() else "degraded",
        database=db_status,
        nlp_index="ready" if is_index_ready() else "not ready",
        index_size=index_size(),
        uptime_seconds=None,
        version=cfg.APP_VERSION,
    )
