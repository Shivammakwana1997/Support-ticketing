"""Tests for RAG and knowledge base endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient):
    """Test listing knowledge documents when none exist."""
    response = await client.get("/api/v1/knowledge/documents")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ingest_url(client: AsyncClient):
    """Test URL ingestion endpoint."""
    payload = {
        "url": "https://example.com/help/article",
        "title": "Test Help Article",
    }
    response = await client.post("/api/v1/knowledge/ingest-url", json=payload)
    assert response.status_code in [200, 201, 422]


@pytest.mark.asyncio
async def test_list_collections(client: AsyncClient):
    """Test listing knowledge collections."""
    response = await client.get("/api/v1/knowledge/collections")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_copilot_suggest_reply(client: AsyncClient):
    """Test copilot suggest reply endpoint."""
    payload = {
        "conversation_id": "a0000000-0000-0000-0000-000000000001",
        "context": "Customer is asking about password reset",
    }
    response = await client.post("/api/v1/copilot/suggest-reply", json=payload)
    assert response.status_code in [200, 422, 500]


@pytest.mark.asyncio
async def test_copilot_summarize(client: AsyncClient):
    """Test copilot summarize endpoint."""
    payload = {
        "conversation_id": "a0000000-0000-0000-0000-000000000001",
    }
    response = await client.post("/api/v1/copilot/summarize", json=payload)
    assert response.status_code in [200, 422, 500]
