from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SuggestReplyRequest(BaseModel):
    conversation_id: UUID
    context: str | None = None
    tone: str = "professional"


class SuggestReplyResponse(BaseModel):
    suggestions: list[str]
    confidence: float = 0.0


class SummarizeRequest(BaseModel):
    conversation_id: UUID | None = None
    ticket_id: UUID | None = None
    text: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    key_points: list[str] = []
    sentiment: str | None = None


class RetrieveKBRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    threshold: float = Field(0.7, ge=0.0, le=1.0)


class RetrieveKBResponse(BaseModel):
    results: list[KBResult]
    query: str


class KBResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    document_title: str | None = None


# Rebuild forward ref
RetrieveKBResponse.model_rebuild()


class TroubleshootingRequest(BaseModel):
    issue_description: str = Field(..., min_length=1)
    product: str | None = None
    customer_id: UUID | None = None


class TroubleshootingResponse(BaseModel):
    steps: list[TroubleshootingStep]
    confidence: float = 0.0
    sources: list[str] = []


class TroubleshootingStep(BaseModel):
    order: int
    title: str
    description: str
    action: str | None = None


# Rebuild forward ref
TroubleshootingResponse.model_rebuild()
