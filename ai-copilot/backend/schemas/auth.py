from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from models.enums import UserRoleEnum


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    tenant_slug: str = Field(..., min_length=1, max_length=255)
    role: UserRoleEnum = UserRoleEnum.AGENT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    display_name: str
    role: UserRoleEnum
    is_active: bool

    model_config = {"from_attributes": True}
