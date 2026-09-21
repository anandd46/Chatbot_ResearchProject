"""Knowledge routes — /api/v1/knowledge"""


import io
import json
import csv as csv_module
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.schemas.knowledge import (
    KnowledgeEntryCreate, KnowledgeEntryOut, KnowledgeEntryUpdate,
    KnowledgeVersionOut, ImportPreview, PaginatedResponse
)
from app.services import knowledge_service
import math

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/", response_model=PaginatedResponse)
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    include_deleted = include_deleted and current_user.role == "admin"
    entries, total = await knowledge_service.get_all_entries(
        db, page, page_size, category, include_deleted
    )
    return PaginatedResponse(
        items=[KnowledgeEntryOut.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )


@router.get("/{entry_id}", response_model=KnowledgeEntryOut)
async def get_entry(entry_id: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    entry = await knowledge_service.get_entry_by_id(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.post("/", response_model=KnowledgeEntryOut, status_code=201)
async def create_entry(
    body: KnowledgeEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    entry = await knowledge_service.create_entry(db, body.model_dump(), str(current_user.id))
    await knowledge_service.rebuild_index(db)
    return entry


@router.put("/{entry_id}", response_model=KnowledgeEntryOut)
async def update_entry(
    entry_id: str,
    body: KnowledgeEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    entry = await knowledge_service.get_entry_by_id(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    updated = await knowledge_service.update_entry(db, entry, body.model_dump(exclude_none=True), str(current_user.id))
    await knowledge_service.rebuild_index(db)
    return updated


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    entry = await knowledge_service.get_entry_by_id(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    await knowledge_service.soft_delete_entry(db, entry, str(current_user.id))
    await knowledge_service.rebuild_index(db)


@router.get("/{entry_id}/versions", response_model=list[KnowledgeVersionOut])
async def get_versions(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    versions = await knowledge_service.get_versions(db, entry_id)
    return [KnowledgeVersionOut.model_validate(v) for v in versions]


@router.post("/reindex", status_code=200)
async def reindex(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    count = await knowledge_service.rebuild_index(db)
    return {"message": f"Index rebuilt with {count} entries", "count": count}


@router.get("/export/json")
async def export_json(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    entries, _ = await knowledge_service.get_all_entries(db, page=1, page_size=10000)
    content = knowledge_service.export_entries_json(entries)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=knowledge_export.json"},
    )


@router.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    entries, _ = await knowledge_service.get_all_entries(db, page=1, page_size=10000)
    content = knowledge_service.export_entries_csv(entries)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=knowledge_export.csv"},
    )


@router.post("/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    _=Depends(require_admin),
):
    content = await file.read()
    try:
        if file.filename.endswith(".json"):
            raw = json.loads(content)
        elif file.filename.endswith(".csv"):
            reader = csv_module.DictReader(io.StringIO(content.decode("utf-8")))
            raw = []
            for row in reader:
                if "keywords" in row:
                    row["keywords"] = [k.strip() for k in row["keywords"].split("|") if k.strip()]
                raw.append(row)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use .json or .csv")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    valid_rows, errors = knowledge_service.validate_import_data(raw)
    return ImportPreview(
        total=len(raw),
        valid=len(valid_rows),
        invalid=len(errors),
        errors=errors[:10],
        preview_rows=valid_rows[:5],
    )


@router.post("/import/confirm")
async def import_confirm(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    rows = body.get("rows", [])
    valid_rows, errors = knowledge_service.validate_import_data(rows)
    created = 0
    for row in valid_rows:
        await knowledge_service.create_entry(db, row, str(current_user.id))
        created += 1
    await knowledge_service.rebuild_index(db)
    return {"imported": created, "errors": len(errors)}
