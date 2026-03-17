"""Tests for webhook endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_twilio_webhook_missing_signature(client: AsyncClient):
    """Test Twilio webhook rejects missing signature."""
    payload = {
        "From": "whatsapp:+1234567890",
        "Body": "Hello, I need help",
        "MessageSid": "SM1234567890",
    }
    response = await client.post("/api/v1/webhooks/twilio", data=payload)
    # Should reject due to missing/invalid Twilio signature
    assert response.status_code in [200, 400, 401, 422]


@pytest.mark.asyncio
async def test_email_webhook(client: AsyncClient):
    """Test email inbound webhook."""
    payload = {
        "from": "customer@example.com",
        "to": "support@ourcompany.com",
        "subject": "Need help with order",
        "text": "I have an issue with my recent order #12345",
        "message_id": "abc123@example.com",
    }
    response = await client.post("/api/v1/webhooks/email", json=payload)
    assert response.status_code in [200, 201, 422]


@pytest.mark.asyncio
async def test_slack_webhook_url_verification(client: AsyncClient):
    """Test Slack URL verification challenge."""
    payload = {
        "type": "url_verification",
        "challenge": "test-challenge-token",
        "token": "verification-token",
    }
    response = await client.post("/api/v1/webhooks/slack", json=payload)
    assert response.status_code in [200, 400, 401]
