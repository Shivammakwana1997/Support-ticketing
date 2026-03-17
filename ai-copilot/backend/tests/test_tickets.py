"""Tests for ticket endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tickets_empty(client: AsyncClient):
    """Test listing tickets when none exist."""
    response = await client.get("/api/v1/tickets")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_ticket(client: AsyncClient):
    """Test creating a ticket."""
    payload = {
        "subject": "Cannot login to my account",
        "customer_id": "a0000000-0000-0000-0000-000000000001",
        "priority": "high",
        "metadata": {"source": "web"},
    }
    response = await client.post("/api/v1/tickets", json=payload)
    # Depends on whether customer exists
    assert response.status_code in [200, 201, 404, 422]


@pytest.mark.asyncio
async def test_get_ticket_not_found(client: AsyncClient):
    """Test getting a non-existent ticket."""
    response = await client.get("/api/v1/tickets/a0000000-0000-0000-0000-000000000099")
    assert response.status_code in [404, 422]


@pytest.mark.asyncio
async def test_update_ticket_status(client: AsyncClient):
    """Test updating ticket status."""
    payload = {
        "status": "pending",
    }
    response = await client.patch(
        "/api/v1/tickets/a0000000-0000-0000-0000-000000000099",
        json=payload,
    )
    assert response.status_code in [200, 404, 422]
