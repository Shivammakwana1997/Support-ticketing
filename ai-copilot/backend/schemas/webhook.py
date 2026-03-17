from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TwilioWebhookPayload(BaseModel):
    MessageSid: str | None = None
    AccountSid: str | None = None
    From: str | None = None
    To: str | None = None
    Body: str | None = None
    NumMedia: str | None = None
    MediaUrl0: str | None = None
    MediaContentType0: str | None = None
    # Voice fields
    CallSid: str | None = None
    CallStatus: str | None = None
    Direction: str | None = None
    RecordingUrl: str | None = None
    RecordingDuration: str | None = None

    model_config = {"extra": "allow"}


class EmailWebhookPayload(BaseModel):
    from_email: str | None = None
    to: str | None = None
    subject: str | None = None
    text: str | None = None
    html: str | None = None
    attachments: list[Any] | None = None
    headers: dict[str, str] | None = None

    model_config = {"extra": "allow"}


class SlackEventPayload(BaseModel):
    token: str | None = None
    team_id: str | None = None
    type: str | None = None
    event: dict[str, Any] | None = None
    challenge: str | None = None
    event_id: str | None = None
    event_time: int | None = None

    model_config = {"extra": "allow"}
