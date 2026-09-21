"""
FastAPI Application Entry Point
================================
Configures:
  - CORS
  - Rate Limiting (SlowAPI)
  - Request ID + Secure Headers middleware
  - All /api/v1 routers
  - Startup: DB init + NLP index build
  - Consistent error response format
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1 import auth, chat, feedback, knowledge, admin, unresolved, evaluation, health
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware, SecureHeadersMiddleware
from app.core.rate_limit import limiter
from app.db.models import Base
from app.db.seed import seed_database
from app.db.session import AsyncSessionLocal, engine
from app.services.knowledge_service import rebuild_index

setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed database if empty
    async with AsyncSessionLocal() as session:
        await seed_database(session)
        await session.commit()

    # Build NLP index
    async with AsyncSessionLocal() as session:
        count = await rebuild_index(session)
        logger.info(f"NLP index ready with {count} entries")

    logger.info("Startup complete")
    yield

    logger.info("Shutting down...")
    await engine.dispose()


# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="Smart College AI Chatbot API — Research-based intelligent virtual assistant",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Rate Limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ── Global Error Handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(SecureHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ── Request Timing Middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(duration, 2))
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health.router)  # /health, /health/live, /health/ready
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(feedback.router, prefix=API_PREFIX)
app.include_router(knowledge.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(unresolved.router, prefix=API_PREFIX)
app.include_router(evaluation.router, prefix=API_PREFIX)


@app.get("/api/v1", tags=["info"])
async def api_info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "college": settings.COLLEGE_NAME,
        "docs": "/api/docs",
    }
