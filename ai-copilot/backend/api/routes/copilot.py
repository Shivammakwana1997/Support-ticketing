"""Copilot API routes - AI assistant for support agents."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError
from models.user import User
from schemas.copilot import (
    SuggestReplyRequest,
    SuggestReplyResponse,
    SummarizeRequest,
    SummarizeResponse,
    RetrieveKBRequest,
    RetrieveKBResponse,
    TroubleshootingRequest,
    TroubleshootingResponse,
)
from services.agents.copilot import copilot_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


@router.post("/suggest-reply", response_model=SuggestReplyResponse)
async def suggest_reply(
    request: SuggestReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestReplyResponse:
    """Get AI-suggested reply for a ticket or conversation."""
    try:
        result = await copilot_service.suggest_reply(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_or_conversation_id=request.ticket_or_conversation_id,
            context=request.context,
        )
        return SuggestReplyResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("suggest_reply_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggested reply",
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummarizeResponse:
    """Get AI-generated summary of a ticket or conversation."""
    try:
        result = await copilot_service.summarize(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_or_conversation_id=request.ticket_or_conversation_id,
        )
        return SummarizeResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("summarize_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary",
        )


@router.post("/retrieve-kb", response_model=RetrieveKBResponse)
async def retrieve_kb(
    request: RetrieveKBRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetrieveKBResponse:
    """Search the knowledge base for relevant articles."""
    try:
        results = await copilot_service.retrieve_kb(
            db=db,
            tenant_id=current_user.tenant_id,
            query=request.query,
        )
        return RetrieveKBResponse(results=results)
    except Exception as e:
        logger.error("retrieve_kb_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge base",
        )


@router.post("/troubleshooting-steps", response_model=TroubleshootingResponse)
async def troubleshooting_steps(
    request: TroubleshootingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TroubleshootingResponse:
    """Get AI-generated troubleshooting steps for a topic or ticket."""
    try:
        result = await copilot_service.troubleshooting_steps(
            db=db,
            tenant_id=current_user.tenant_id,
            topic_or_ticket_id=request.topic_or_ticket_id,
        )
        return TroubleshootingResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("troubleshooting_steps_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate troubleshooting steps",
        )
