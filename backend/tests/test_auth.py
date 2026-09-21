"""Tests for authentication routes."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "password": "NewUser@123",
        "name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "weak@test.com",
        "password": "weakpassword",
        "name": "Weak User",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dupe@test.com", "password": "Dupe@Pass1", "name": "User 1"
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dupe@test.com", "password": "Dupe@Pass1", "name": "User 2"
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com", "password": "Login@Pass1", "name": "Login User"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com", "password": "Login@Pass1"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "pwtest@test.com", "password": "Right@Pass1", "name": "PW Test"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "pwtest@test.com", "password": "Wrong@Pass1"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, user_token: str):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "student@test.com"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_protected_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "refresh@test.com", "password": "Refresh@1", "name": "Refresh"
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "logout@test.com", "password": "Logout@1X", "name": "Logout"
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204
    # Refresh after logout should fail
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401
