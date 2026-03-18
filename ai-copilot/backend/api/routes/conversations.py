"""Conversation management routes."""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError, ForbiddenError
from models.user import User
from models.enums import ConversationStatusEnum, ChannelEnum
from schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from schemas.message import MessageCreate, MessageResponse
from schemas.common import PaginatedResponse
from services.conversation import conversation_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.get("", response_model=PaginatedResponse)
async def list_conversations(
    status_filter: Optional[ConversationStatusEnum] = Query(None, alias="status"),
    customer_id: Optional[str] = Query(None),
    channel: Optional[ChannelEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse:
    """List conversations with pagination and filters."""
    try:
        result = await conversation_service.list_conversations(
            db=db,
            tenant_id=current_user.tenant_id,
            status=status_filter,
            customer_id=customer_id,
            channel=channel,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        logger.error("list_conversations_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Create a new conversation."""
    try:
        conversation = await conversation_service.create_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            customer_id=request.customer_id,
            channel=request.channel,
            metadata=request.metadata,
        )
        logger.info(
            "conversation_created",
            conversation_id=conversation.id if hasattr(conversation, "id") else str(conversation),
            tenant_id=current_user.tenant_id,
        )
        return ConversationResponse.model_validate(conversation)
    except Exception as e:
        logger.error("create_conversation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Get a conversation by ID with messages."""
    try:
        result = await conversation_service.get_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
        )
        return ConversationResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "get_conversation_failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    """Update a conversation."""
    try:
        conversation = await conversation_service.update_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
            data=request.model_dump(exclude_unset=True),
        )
        logger.info("conversation_updated", conversation_id=conversation_id)
        return ConversationResponse.model_validate(conversation)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "update_conversation_failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    """Get messages for a conversation."""
    try:
        result = await conversation_service.get_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
        )
        messages = result.get("messages", [])
        return [MessageResponse.model_validate(m) for m in messages]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "get_conversation_messages_failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation messages",
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_conversation_message(
    conversation_id: str,
    request: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Add a message to a conversation."""
    try:
        message = await conversation_service.add_message(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
            sender_type=request.sender_type,
            sender_id=str(current_user.id),
            content=request.content,
            channel=request.channel,
        )
        return MessageResponse.model_validate(message)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "add_conversation_message_failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message",
        )
