"""Tests for chat endpoint."""
import pytest
from httpx import AsyncClient

from app.nlp.retriever import build_index


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/chat/send", json={"message": "Hello"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_empty_message(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/v1/chat/send",
        json={"message": ""},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_chat_returns_response(client: AsyncClient, user_token: str):
    # Seed a minimal index so pipeline can find something
    build_index([{
        "id": "test-id-001",
        "category": "admissions",
        "question": "How do I apply for admission?",
        "answer": "You can apply online.",
        "keywords": ["apply", "admission"],
    }])

    resp = await client.post(
        "/api/v1/chat/send",
        json={"message": "How do I apply for admission?"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "session_id" in data
    assert "message_id" in data
    assert "intent" in data
    assert "confidence" in data
    assert "query_type" in data


@pytest.mark.asyncio
async def test_chat_ood_detected(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/v1/chat/send",
        json={"message": "What is the cricket score today?"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["query_type"] == "OUT_OF_DOMAIN"


@pytest.mark.asyncio
async def test_chat_session_continuity(client: AsyncClient, user_token: str):
    # First message creates session
    r1 = await client.post(
        "/api/v1/chat/send",
        json={"message": "Tell me about the college"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    session_id = r1.json()["session_id"]

    # Second message uses same session
    r2 = await client.post(
        "/api/v1/chat/send",
        json={"message": "What are the fee details?", "session_id": session_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/health/live")).status_code == 200
    # /health/ready might not be fully ready in test env, just check it responds
    resp = await client.get("/health/ready")
    assert resp.status_code in (200, 200)  # Accept ok or not-ready JSON
    assert "status" in resp.json()
