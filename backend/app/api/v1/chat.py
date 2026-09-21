"""Chat routes — /api/v1/chat"""


from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ConversationOut, MessageOut
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def send_message(
    request: Request,
    body: ChatRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = await chat_service.process_message(
        db=db,
        user_id=str(current_user.id),
        session_id=body.session_id,
        query=body.message.strip(),
    )
    return result


@router.get("/sessions", response_model=list[ConversationOut])
async def get_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
):
    convs = await chat_service.get_user_conversations(db, str(current_user.id), page)
    return [
        ConversationOut(
            id=str(c.id),
            title=c.title,
            started_at=c.started_at,
        )
        for c in convs
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await chat_service.get_conversation_messages(db, session_id, str(current_user.id))
    return [
        MessageOut(
            id=str(m.id),
            role=m.role,
            content=m.content,
            intent=m.intent,
            confidence=m.confidence,
            query_type=m.query_type,
            processing_time_ms=m.processing_time_ms,
            created_at=m.created_at,
        )
        for m in messages
    ]
