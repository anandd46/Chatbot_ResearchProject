"""
Authentication service — register, login, refresh, logout.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password,
    verify_password,
)
from app.core.config import settings
from app.db.models import RefreshToken, User, UserRole

logger = get_logger(__name__)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str,
    role: str = "student",
) -> User:
    # Validate password policy
    validate_password(password)

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalars().first():
        raise ValueError("An account with this email already exists.")

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        name=name,
        role=UserRole(role),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalars().first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    return user


async def create_tokens(db: AsyncSession, user: User) -> dict:
    access_token = create_access_token(
        str(user.id),
        extra_claims={"role": user.role, "name": user.name, "email": user.email},
    )
    refresh_token_raw = create_refresh_token()
    token_hash = _hash_refresh_token(refresh_token_raw)

    rt = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(rt)
    await db.flush()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_raw,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def refresh_tokens(db: AsyncSession, refresh_token_raw: str) -> dict:
    token_hash = _hash_refresh_token(refresh_token_raw)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
    )
    rt = result.scalars().first()

    if not rt or rt.expires_at < datetime.now(timezone.utc):
        raise ValueError("Invalid or expired refresh token.")

    # Revoke old token
    rt.revoked = True

    # Get user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalars().first()
    if not user or not user.is_active:
        raise ValueError("User not found or inactive.")

    return await create_tokens(db, user)


async def logout_user(db: AsyncSession, refresh_token_raw: str) -> None:
    token_hash = _hash_refresh_token(refresh_token_raw)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalars().first()
    if rt:
        rt.revoked = True


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalars().first()
