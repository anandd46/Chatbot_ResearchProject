"""Feedback routes — /api/v1/feedback"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps import get_current_user, require_admin
from app.db.models import Feedback, Message
from app.db.session import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackOut, status_code=201)
async def submit_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Verify message exists
    msg_result = await db.execute(select(Message).where(Message.id == uuid.UUID(body.message_id)))
    msg = msg_result.scalars().first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check duplicate
    existing = await db.execute(
        select(Feedback).where(
            Feedback.message_id == uuid.UUID(body.message_id),
            Feedback.user_id == current_user.id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Feedback already submitted for this message")

    fb = Feedback(
        id=uuid.uuid4(),
        message_id=uuid.UUID(body.message_id),
        user_id=current_user.id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(fb)
    await db.flush()
    return FeedbackOut.model_validate(fb)


@router.get("/", response_model=list[FeedbackOut])
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return [FeedbackOut.model_validate(f) for f in result.scalars().all()]
