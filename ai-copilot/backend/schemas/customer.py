from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    external_id: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    display_name: str = Field(..., min_length=1, max_length=255)
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class CustomerUpdate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    display_name: str | None = Field(None, min_length=1, max_length=255)
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class CustomerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    external_id: str | None
    email: str | None
    phone: str | None
    display_name: str
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class CustomerContextResponse(BaseModel):
    customer: CustomerResponse
    recent_tickets: list[Any] = []
    recent_conversations: list[Any] = []
    total_tickets: int = 0
    total_conversations: int = 0

    model_config = {"from_attributes": True}
