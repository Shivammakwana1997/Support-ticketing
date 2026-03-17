from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.models.enums import ChannelEnum, SenderTypeEnum


class MessageCreate(BaseModel):
    sender_type: SenderTypeEnum
    sender_id: UUID | None = None
    channel: ChannelEnum
    content: str = Field(..., min_length=1)
    content_type: str = "text"
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class MessageResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    sender_type: SenderTypeEnum
    sender_id: UUID | None
    channel: ChannelEnum
    content: str
    content_type: str
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
