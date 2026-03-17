from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from backend.models.enums import DocumentStatusEnum


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_ref: str | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class DocumentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    source_type: str
    source_ref: str | None
    status: DocumentStatusEnum
    version: int
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class CollectionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    document_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestURLRequest(BaseModel):
    url: HttpUrl
    title: str | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
