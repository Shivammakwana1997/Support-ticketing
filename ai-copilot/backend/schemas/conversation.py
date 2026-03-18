from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from models.enums import ChannelEnum, ConversationStatusEnum


class ConversationCreate(BaseModel):
    customer_id: UUID
    channel: ChannelEnum
    assigned_agent_id: UUID | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class ConversationUpdate(BaseModel):
    status: ConversationStatusEnum | None = None
    assigned_agent_id: UUID | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class ConversationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    channel: ChannelEnum
    status: ConversationStatusEnum
    assigned_agent_id: UUID | None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}
