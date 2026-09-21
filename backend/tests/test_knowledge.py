"""Tests for knowledge base routes."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_knowledge_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/knowledge/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_knowledge_requires_admin(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/v1/knowledge/",
        json={"category": "test", "question": "Q?", "answer": "A."},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_knowledge_as_admin(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/knowledge/",
        json={
            "category": "general",
            "question": "What is the college name?",
            "answer": "Greenfield Institute of Technology",
            "keywords": ["college", "name"],
            "reason": "Test entry",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "general"
    assert data["version_count"] == 1
    return data["id"]


@pytest.mark.asyncio
async def test_update_knowledge_creates_version(client: AsyncClient, admin_token: str):
    # Create first
    create_resp = await client.post(
        "/api/v1/knowledge/",
        json={"category": "test", "question": "Original Q?", "answer": "Original A."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    entry_id = create_resp.json()["id"]

    # Update
    update_resp = await client.put(
        f"/api/v1/knowledge/{entry_id}",
        json={"answer": "Updated A.", "reason": "Corrected answer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["version_count"] == 2


@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient, admin_token: str, user_token: str):
    create_resp = await client.post(
        "/api/v1/knowledge/",
        json={"category": "test", "question": "To delete?", "answer": "Delete me."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    entry_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/knowledge/{entry_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 204

    # Should no longer appear in default list
    list_resp = await client.get(
        "/api/v1/knowledge/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert entry_id not in ids


@pytest.mark.asyncio
async def test_reindex(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/knowledge/reindex",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert "count" in resp.json()
