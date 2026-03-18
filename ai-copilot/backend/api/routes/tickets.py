"""Ticket management routes."""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError, ForbiddenError
from models.user import User
from models.enums import TicketStatusEnum, PriorityEnum
from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
)
from schemas.message import MessageCreate, MessageResponse
from schemas.common import PaginatedResponse
from services.ticketing import ticketing_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])

from pydantic import BaseModel
import uuid

class DemoTicketRequest(BaseModel):
    message: str

# In-memory storage for the demo since we don't have Supabase fully connected in the sandbox
DEMO_TICKETS = []

@router.post("/demo-create")
async def create_demo_ticket(request: DemoTicketRequest):
    """Mocks ticket creation with AI intent classification for the demo."""
    from services.nlp.intent import intent_service
    from models.enums import TicketCategoryEnum, PriorityEnum
    from services.ticketing import _generate_ticket_number

    try:
        intent_result = await intent_service.detect_intent(request.message)
        detected_intent = intent_result.intent
    except Exception:
        # Fallback if OpenAI fails in demo sandbox
        if "fraud" in request.message.lower() or "stolen" in request.message.lower():
            detected_intent = "fraud"
        else:
            detected_intent = "general"

    category = TicketCategoryEnum.GENERAL
    priority = PriorityEnum.MEDIUM

    if detected_intent == "fraud":
        priority = PriorityEnum.URGENT
        category = TicketCategoryEnum.FRAUD
    elif detected_intent == "otp_issue":
        priority = PriorityEnum.HIGH
        category = TicketCategoryEnum.OTP_ISSUE
    elif detected_intent == "password_reset":
        priority = PriorityEnum.HIGH
        category = TicketCategoryEnum.PASSWORD_RESET
    elif detected_intent == "technical":
        priority = PriorityEnum.MEDIUM
        category = TicketCategoryEnum.TECHNICAL

    ticket = {
        "id": str(uuid.uuid4()),
        "ticket_number": _generate_ticket_number(),
        "subject": request.message,
        "category": category,
        "priority": priority,
        "status": "open"
    }

    DEMO_TICKETS.insert(0, ticket)
    return ticket

@router.get("/demo-list")
async def list_demo_tickets():
    """Returns the mocked demo tickets."""
    return DEMO_TICKETS



@router.get("", response_model=PaginatedResponse)
async def list_tickets(
    status_filter: Optional[TicketStatusEnum] = Query(None, alias="status"),
    priority: Optional[PriorityEnum] = Query(None),
    assigned_to: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse:
    """List tickets with pagination and filters."""
    try:
        result = await ticketing_service.list_tickets(
            db=db,
            tenant_id=current_user.tenant_id,
            status=status_filter,
            priority=priority,
            assigned_to=assigned_to,
            customer_id=customer_id,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        logger.error("list_tickets_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tickets",
        )


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    """Create a new support ticket."""
    try:
        ticket = await ticketing_service.create_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            customer_id=request.customer_id,
            subject=request.subject,
            description=request.description,
            conversation_id=request.conversation_id,
            priority=request.priority,
            metadata=request.metadata,
        )
        logger.info(
            "ticket_created",
            ticket_id=ticket.id if hasattr(ticket, "id") else str(ticket),
            tenant_id=current_user.tenant_id,
        )
        return TicketResponse.model_validate(ticket)
    except Exception as e:
        logger.error("create_ticket_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket",
        )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketDetailResponse:
    """Get a ticket by ID with messages."""
    try:
        result = await ticketing_service.get_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
        )
        return TicketDetailResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_ticket_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ticket",
        )


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    request: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    """Update a ticket."""
    try:
        ticket = await ticketing_service.update_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
            data=request.model_dump(exclude_unset=True),
        )
        logger.info("ticket_updated", ticket_id=ticket_id)
        return TicketResponse.model_validate(ticket)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_ticket_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket",
        )


@router.get("/{ticket_id}/messages", response_model=list[MessageResponse])
async def get_ticket_messages(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    """Get messages for a ticket."""
    try:
        result = await ticketing_service.get_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
        )
        messages = result.get("messages", [])
        return [MessageResponse.model_validate(m) for m in messages]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_ticket_messages_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ticket messages",
        )


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_ticket_message(
    ticket_id: str,
    request: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Add a message to a ticket."""
    try:
        # Get ticket to find conversation_id
        ticket_data = await ticketing_service.get_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
        )
        ticket = ticket_data.get("ticket")
        conversation_id = getattr(ticket, "conversation_id", None) if ticket else None

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket has no associated conversation",
            )

        from services.conversation import conversation_service

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("add_ticket_message_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message",
        )


from pydantic import BaseModel

class TicketSummaryResponse(BaseModel):
    summary: str

@router.get("/{ticket_id}/summary", response_model=TicketSummaryResponse)
async def get_ticket_summary(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketSummaryResponse:
    """Get an AI-generated summary of a ticket."""
    try:
        summary = await ticketing_service.get_ticket_summary(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
        )
        return TicketSummaryResponse(**summary)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_ticket_summary_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate ticket summary",
        )


class TicketRouteResponse(BaseModel):
    assigned_agent_id: str | None

@router.post("/{ticket_id}/route", response_model=TicketRouteResponse)
async def route_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRouteResponse:
    """Route a ticket to the best available agent."""
    try:
        result = await ticketing_service.route_ticket(
            db=db,
            tenant_id=current_user.tenant_id,
            ticket_id=ticket_id,
        )
        return TicketRouteResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("route_ticket_failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to route ticket",
        )
