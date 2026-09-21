"""
Knowledge service — CRUD, versioning, soft delete, import/export, reindex.
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import KnowledgeEntry, KnowledgeVersion
from app.nlp import build_index

logger = get_logger(__name__)


async def get_all_entries(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    include_deleted: bool = False,
    include_inactive: bool = False,
) -> Tuple[List[KnowledgeEntry], int]:
    query = select(KnowledgeEntry)
    if not include_deleted:
        query = query.where(KnowledgeEntry.is_deleted == False)
    if not include_inactive:
        query = query.where(KnowledgeEntry.is_active == True)
    if category:
        query = query.where(KnowledgeEntry.category == category)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = query.order_by(KnowledgeEntry.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_entry_by_id(db: AsyncSession, entry_id: str) -> Optional[KnowledgeEntry]:
    result = await db.execute(
        select(KnowledgeEntry).where(
            KnowledgeEntry.id == uuid.UUID(entry_id),
            KnowledgeEntry.is_deleted == False,
        )
    )
    return result.scalars().first()


async def create_entry(
    db: AsyncSession,
    data: Dict,
    created_by: str,
) -> KnowledgeEntry:
    entry_id = uuid.uuid4()
    entry = KnowledgeEntry(
        id=entry_id,
        category=data["category"],
        question=data["question"],
        answer=data["answer"],
        keywords=data.get("keywords", []),
        source_title=data.get("source_title"),
        source_url=data.get("source_url"),
        source_type=data.get("source_type"),
        last_verified=data.get("last_verified") or datetime.now(timezone.utc),
        is_active=True,
        is_deleted=False,
        version_count=1,
        created_by=uuid.UUID(created_by),
        updated_by=uuid.UUID(created_by),
    )
    db.add(entry)

    version = KnowledgeVersion(
        id=uuid.uuid4(),
        entry_id=entry_id,
        version=1,
        question=data["question"],
        answer=data["answer"],
        keywords=data.get("keywords", []),
        changed_by=uuid.UUID(created_by),
        reason=data.get("reason", "Initial entry"),
    )
    db.add(version)
    await db.flush()
    return entry


async def update_entry(
    db: AsyncSession,
    entry: KnowledgeEntry,
    data: Dict,
    updated_by: str,
) -> KnowledgeEntry:
    old_version = entry.version_count

    for field in ["category", "question", "answer", "keywords",
                  "source_title", "source_url", "source_type",
                  "last_verified", "is_active"]:
        if field in data and data[field] is not None:
            setattr(entry, field, data[field])

    entry.version_count = old_version + 1
    entry.updated_by = uuid.UUID(updated_by)
    entry.updated_at = datetime.now(timezone.utc)

    version = KnowledgeVersion(
        id=uuid.uuid4(),
        entry_id=entry.id,
        version=old_version + 1,
        question=entry.question,
        answer=entry.answer,
        keywords=entry.keywords,
        changed_by=uuid.UUID(updated_by),
        reason=data.get("reason", "Updated"),
    )
    db.add(version)
    await db.flush()
    return entry


async def soft_delete_entry(
    db: AsyncSession, entry: KnowledgeEntry, deleted_by: str
) -> None:
    entry.is_deleted = True
    entry.is_active = False
    entry.updated_by = uuid.UUID(deleted_by)
    entry.updated_at = datetime.now(timezone.utc)

    version = KnowledgeVersion(
        id=uuid.uuid4(),
        entry_id=entry.id,
        version=entry.version_count + 1,
        question=entry.question,
        answer=entry.answer,
        keywords=entry.keywords,
        changed_by=uuid.UUID(deleted_by),
        reason="Soft deleted",
    )
    db.add(version)
    entry.version_count += 1


async def get_versions(
    db: AsyncSession, entry_id: str
) -> List[KnowledgeVersion]:
    result = await db.execute(
        select(KnowledgeVersion)
        .where(KnowledgeVersion.entry_id == uuid.UUID(entry_id))
        .order_by(KnowledgeVersion.version.desc())
    )
    return result.scalars().all()


async def rebuild_index(db: AsyncSession) -> int:
    """Rebuild TF-IDF index from all active, non-deleted KB entries."""
    result = await db.execute(
        select(KnowledgeEntry).where(
            KnowledgeEntry.is_active == True,
            KnowledgeEntry.is_deleted == False,
        )
    )
    entries = result.scalars().all()

    entry_dicts = [
        {
            "id": str(e.id),
            "category": e.category,
            "question": e.question,
            "answer": e.answer,
            "keywords": e.keywords or [],
            "source_title": e.source_title,
            "source_url": e.source_url,
        }
        for e in entries
    ]
    build_index(entry_dicts)
    logger.info(f"Index rebuilt with {len(entry_dicts)} entries")
    return len(entry_dicts)


def export_entries_json(entries: List[KnowledgeEntry]) -> str:
    data = [
        {
            "category": e.category,
            "question": e.question,
            "answer": e.answer,
            "keywords": e.keywords or [],
            "source_title": e.source_title or "",
            "source_url": e.source_url or "",
            "source_type": e.source_type or "",
        }
        for e in entries
    ]
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_entries_csv(entries: List[KnowledgeEntry]) -> str:
    output = io.StringIO()
    fieldnames = ["category", "question", "answer", "keywords", "source_title", "source_url", "source_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for e in entries:
        writer.writerow({
            "category": e.category,
            "question": e.question,
            "answer": e.answer,
            "keywords": "|".join(e.keywords or []),
            "source_title": e.source_title or "",
            "source_url": e.source_url or "",
            "source_type": e.source_type or "",
        })
    return output.getvalue()


def validate_import_data(raw: Any) -> Tuple[List[Dict], List[str]]:
    """Validate import data, return (valid_rows, errors)."""
    valid_rows = []
    errors = []

    if not isinstance(raw, list):
        return [], ["Root element must be a JSON array"]

    required_fields = {"category", "question", "answer"}

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"Row {i}: not a JSON object")
            continue
        missing = required_fields - set(item.keys())
        if missing:
            errors.append(f"Row {i}: missing required fields: {missing}")
            continue
        if not item.get("question", "").strip():
            errors.append(f"Row {i}: question is empty")
            continue
        if not item.get("answer", "").strip():
            errors.append(f"Row {i}: answer is empty")
            continue
        valid_rows.append(item)

    return valid_rows, errors
