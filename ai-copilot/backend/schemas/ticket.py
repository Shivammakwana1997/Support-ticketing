from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from models.enums import PriorityEnum, TicketStatusEnum, TicketCategoryEnum


class TicketCreate(BaseModel):
    customer_id: UUID
    conversation_id: UUID | None = None
    subject: str = Field(..., min_length=1, max_length=500)
    priority: PriorityEnum = PriorityEnum.MEDIUM
    assigned_agent_id: UUID | None = None
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class TicketUpdate(BaseModel):
    subject: str | None = Field(None, min_length=1, max_length=500)
    status: TicketStatusEnum | None = None
    priority: PriorityEnum | None = None
    category: TicketCategoryEnum | None = None
    assigned_agent_id: UUID | None = None
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class TicketResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID | None
    customer_id: UUID
    subject: str
    status: TicketStatusEnum
    priority: PriorityEnum
    category: TicketCategoryEnum
    assigned_agent_id: UUID | None
    sla_due_at: datetime | None
    sla_breach_at: datetime | None
    summary: str | None
    tags: list[str] | None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class TicketSummaryResponse(BaseModel):
    ticket_id: UUID
    summary: str
    key_points: list[str] = []
    sentiment: str | None = None
