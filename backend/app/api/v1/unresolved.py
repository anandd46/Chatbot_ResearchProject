"""Unresolved query routes — /api/v1/unresolved"""


import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.models import UnresolvedQuery, UnresolvedStatus
from app.db.session import get_db
from app.schemas.unresolved import ConvertToKbRequest, UnresolvedQueryOut, UnresolvedQueryUpdate
from app.services import knowledge_service
from datetime import datetime, timezone

router = APIRouter(prefix="/unresolved", tags=["unresolved"])


@router.get("/", response_model=list[UnresolvedQueryOut])
async def list_unresolved(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    query = select(UnresolvedQuery).order_by(UnresolvedQuery.created_at.desc())
    if status:
        query = query.where(UnresolvedQuery.status == status)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [UnresolvedQueryOut.model_validate(u) for u in result.scalars().all()]


@router.patch("/{query_id}", response_model=UnresolvedQueryOut)
async def update_unresolved(
    query_id: str,
    body: UnresolvedQueryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(UnresolvedQuery).where(UnresolvedQuery.id == uuid.UUID(query_id))
    )
    uq = result.scalars().first()
    if not uq:
        raise HTTPException(status_code=404, detail="Unresolved query not found")

    if body.status:
        uq.status = body.status
        if body.status == UnresolvedStatus.RESOLVED:
            uq.resolved_by = current_user.id
            uq.resolved_at = datetime.now(timezone.utc)
    if body.admin_notes is not None:
        uq.admin_notes = body.admin_notes

    await db.flush()
    return UnresolvedQueryOut.model_validate(uq)


@router.post("/{query_id}/convert", status_code=201)
async def convert_to_kb(
    query_id: str,
    body: ConvertToKbRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(UnresolvedQuery).where(UnresolvedQuery.id == uuid.UUID(query_id))
    )
    uq = result.scalars().first()
    if not uq:
        raise HTTPException(status_code=404, detail="Unresolved query not found")

    # Create KB entry
    entry = await knowledge_service.create_entry(
        db,
        {
            "category": body.category,
            "question": body.question or uq.query,
            "answer": body.answer,
            "keywords": body.keywords,
            "source_title": body.source_title,
            "source_url": body.source_url,
            "source_type": body.source_type,
            "reason": f"Converted from unresolved query #{query_id[:8]}",
        },
        str(current_user.id),
    )

    # Resolve the unresolved query
    uq.status = UnresolvedStatus.RESOLVED
    uq.resolved_by = current_user.id
    uq.resolved_at = datetime.now(timezone.utc)
    uq.kb_entry_id = entry.id
    uq.admin_notes = (uq.admin_notes or "") + f"\nConverted to KB entry: {entry.id}"

    await knowledge_service.rebuild_index(db)
    return {"message": "Knowledge entry created and index rebuilt", "entry_id": str(entry.id)}
