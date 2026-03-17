from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from backend.models.enums import UserRoleEnum


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRoleEnum = UserRoleEnum.AGENT
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRoleEnum | None = None
    is_active: bool | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    display_name: str
    role: UserRoleEnum
    is_active: bool
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
