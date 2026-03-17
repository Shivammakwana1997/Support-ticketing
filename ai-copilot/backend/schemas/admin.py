from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AIConfigResponse(BaseModel):
    model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.7
    max_tokens: int = 1024
    system_prompt: str | None = None
    rag_top_k: int = 5
    rag_threshold: float = 0.7


class AIConfigUpdate(BaseModel):
    model: str | None = None
    embedding_model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=128000)
    system_prompt: str | None = None
    rag_top_k: int | None = Field(None, ge=1, le=50)
    rag_threshold: float | None = Field(None, ge=0.0, le=1.0)


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = []
    expires_at: datetime | None = None


class APIKeyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    key_prefix: str  # first 8 chars of the key for identification
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    raw_key: str  # only returned on creation


class UsageResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_api_calls: int = 0
    total_tokens_used: int = 0
    total_embeddings: int = 0
    total_voice_minutes: float = 0.0
    breakdown: dict[str, Any] = {}
