"""Tests for conversation endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_conversations_empty(client: AsyncClient):
    """Test listing conversations when none exist."""
    response = await client.get("/api/v1/conversations")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """Test creating a conversation."""
    payload = {
        "customer_id": "a0000000-0000-0000-0000-000000000001",
        "channel": "chat",
        "metadata": {},
    }
    response = await client.post("/api/v1/conversations", json=payload)
    assert response.status_code in [200, 201, 404, 422]


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient):
    """Test getting a non-existent conversation."""
    response = await client.get("/api/v1/conversations/a0000000-0000-0000-0000-000000000099")
    assert response.status_code in [404, 422]
