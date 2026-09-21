"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db: AsyncSession):
    """Create an admin user and return their JWT token."""
    from app.core.security import hash_password
    from app.db.models import User, UserRole
    import uuid

    user = User(
        id=uuid.uuid4(),
        email="testadmin@test.com",
        hashed_password=hash_password("Admin@Test1"),
        name="Test Admin",
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    await db.commit()

    resp = await client.post("/api/v1/auth/login", json={"email": "testadmin@test.com", "password": "Admin@Test1"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, db: AsyncSession):
    """Register a student user and return their JWT token."""
    resp = await client.post("/api/v1/auth/register", json={
        "email": "student@test.com", "password": "Student@Test1", "name": "Test Student"
    })
    return resp.json()["access_token"]
