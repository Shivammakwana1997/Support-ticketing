"""Customer management routes."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError
from models.user import User
from schemas.customer import CustomerResponse, CustomerContextResponse
from schemas.ticket import TicketResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerResponse:
    """Get customer details."""
    try:
        from repositories.customer import CustomerRepository

        repo = CustomerRepository()
        customer = await repo.get_by_id(db, customer_id)

        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        if getattr(customer, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Customer {customer_id} not found")

        return CustomerResponse.model_validate(customer)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_customer_failed", customer_id=customer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer",
        )


@router.get("/{customer_id}/tickets", response_model=list[TicketResponse])
async def get_customer_tickets(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketResponse]:
    """Get all tickets for a customer."""
    try:
        from repositories.ticket import TicketRepository

        repo = TicketRepository()
        tickets = await repo.list_by_customer(
            db,
            tenant_id=current_user.tenant_id,
            customer_id=customer_id,
        )
        return [TicketResponse.model_validate(t) for t in tickets]
    except Exception as e:
        logger.error(
            "get_customer_tickets_failed",
            customer_id=customer_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer tickets",
        )


@router.get("/{customer_id}/context", response_model=CustomerContextResponse)
async def get_customer_context(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerContextResponse:
    """Get full customer context - profile, recent tickets, conversations, and sentiment."""
    try:
        from repositories.customer import CustomerRepository
        from repositories.ticket import TicketRepository
        from repositories.conversation import ConversationRepository

        customer_repo = CustomerRepository()
        ticket_repo = TicketRepository()
        conversation_repo = ConversationRepository()

        tenant_id = current_user.tenant_id

        # Fetch customer
        customer = await customer_repo.get_by_id(db, customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        if getattr(customer, "tenant_id", None) != tenant_id:
            raise NotFoundError(f"Customer {customer_id} not found")

        # Fetch recent tickets
        tickets = await ticket_repo.list_by_customer(
            db,
            tenant_id=tenant_id,
            customer_id=customer_id,
        )

        # Fetch recent conversations
        conversations = await conversation_repo.list_by_customer(
            db,
            tenant_id=tenant_id,
            customer_id=customer_id,
        )

        # Build context
        total_tickets = len(tickets) if tickets else 0
        open_tickets = sum(
            1 for t in (tickets or [])
            if getattr(t, "status", None) in ("open", "pending")
        )

        return CustomerContextResponse(
            customer=CustomerResponse.model_validate(customer),
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            recent_tickets=[
                TicketResponse.model_validate(t) for t in (tickets or [])[:5]
            ],
            total_conversations=len(conversations) if conversations else 0,
            recent_conversations=[
                {"id": getattr(c, "id", ""), "status": getattr(c, "status", ""), "channel": getattr(c, "channel", "")}
                for c in (conversations or [])[:5]
            ],
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "get_customer_context_failed",
            customer_id=customer_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer context",
        )
