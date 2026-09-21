"""
Application configuration — all values sourced from environment variables.
No hardcoded secrets. Copy .env.example to .env and fill in real values.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Smart College AI Chatbot"
    APP_ENV: str = "development"
    DEBUG: bool = False
    APP_VERSION: str = "1.0.0"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://chatbot_user:changeme@localhost:5432/chatbot_db"
    )

    # ── JWT / Security ───────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "INSECURE_DEFAULT_CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Password Policy ──────────────────────────────────────────────────────
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # ── Rate Limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_CHAT: str = "20/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_GENERAL: str = "100/minute"

    # ── NLP ──────────────────────────────────────────────────────────────────
    NLP_CONFIDENCE_THRESHOLD: float = 0.35
    OOD_CONFIDENCE_THRESHOLD: float = 0.10
    SCORE_WEIGHT_TFIDF: float = 0.40
    SCORE_WEIGHT_WORD_ORDER: float = 0.25
    SCORE_WEIGHT_INTENT: float = 0.20
    SCORE_WEIGHT_KEYWORD: float = 0.15

    # ── Admin Seed ───────────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@college.edu"
    ADMIN_PASSWORD: str = "Admin@1234"
    ADMIN_NAME: str = "System Administrator"

    # ── College Branding ─────────────────────────────────────────────────────
    COLLEGE_NAME: str = "Greenfield Institute of Technology"
    COLLEGE_SHORT_NAME: str = "GIT"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v

    # ── Optional LLM ─────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "local"  # local | openai | gemini

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic migrations."""
        if self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL.replace("+aiosqlite", "")
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace(
            "postgresql+asyncpg", "postgresql"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
