"""Health check routes — /health, /health/live, /health/ready"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.nlp.retriever import index_size, is_index_ready

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@router.get("/health/live")
async def liveness():
    """Always returns 200 if the process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Returns 200 only when DB is reachable and NLP index is loaded."""
    checks = {}
    all_ok = True

    # DB check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        all_ok = False

    # NLP index check
    checks["nlp_index"] = "ready" if is_index_ready() else "not ready"
    checks["index_size"] = index_size()
    if not is_index_ready():
        all_ok = False

    return {
        "status": "ready" if all_ok else "not ready",
        "checks": checks,
    }
