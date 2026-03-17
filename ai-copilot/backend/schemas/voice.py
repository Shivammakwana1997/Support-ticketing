from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    audio_url: str | None = None
    audio_base64: str | None = None
    language: str = "en"


class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration_seconds: float | None = None
    segments: list[TranscriptSegment] = []


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str | None = None


# Rebuild forward ref
TranscribeResponse.model_rebuild()


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice: str = "alloy"
    format: str = "mp3"


class SynthesizeResponse(BaseModel):
    audio_url: str | None = None
    audio_base64: str | None = None
    duration_seconds: float | None = None


class VoiceCallCreate(BaseModel):
    customer_id: UUID
    conversation_id: UUID | None = None
    agent_id: UUID | None = None
    external_id: str | None = None


class VoiceCallResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID | None
    customer_id: UUID
    agent_id: UUID | None
    external_id: str | None
    recording_url: str | None
    transcript: str | None
    summary: str | None
    duration_seconds: int | None
    sentiment_score: float | None
    created_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class CallSummaryResponse(BaseModel):
    call_id: UUID
    summary: str
    key_points: list[str] = []
    sentiment: str | None = None
    action_items: list[str] = []
