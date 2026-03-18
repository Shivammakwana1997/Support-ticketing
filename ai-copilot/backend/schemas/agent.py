from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from models.enums import AgentStatusEnum


class AgentCreate(BaseModel):
    user_id: UUID
    display_name: str = Field(..., min_length=1, max_length=255)
    status: AgentStatusEnum = AgentStatusEnum.OFFLINE
    skills: list[str] | None = None


class AgentUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    status: AgentStatusEnum | None = None
    skills: list[str] | None = None


class AgentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    display_name: str
    status: AgentStatusEnum
    skills: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
