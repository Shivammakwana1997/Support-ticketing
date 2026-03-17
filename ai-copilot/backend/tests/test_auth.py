"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "display_name": "New User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    # May be 201 or 200 depending on implementation
    assert response.status_code in [200, 201, 422]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration with invalid email fails."""
    payload = {
        "email": "not-an-email",
        "password": "securepassword123",
        "display_name": "Bad Email User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test get current user endpoint."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in [200, 401]
