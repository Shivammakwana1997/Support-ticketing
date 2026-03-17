from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.enums import TicketStatusEnum
from backend.models.ticket import Ticket
from backend.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Ticket, session)

    async def get_by_status(
        self,
        status: TicketStatusEnum,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.status == status)
            .where(Ticket.tenant_id == tenant_id)
            .order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_customer(
        self, customer_id: UUID, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.customer_id == customer_id)
            .where(Ticket.tenant_id == tenant_id)
            .order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_agent(
        self, agent_id: UUID, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.assigned_agent_id == agent_id)
            .where(Ticket.tenant_id == tenant_id)
            .order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_sla_breaching(self, tenant_id: UUID) -> Sequence[Ticket]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Ticket)
            .where(Ticket.tenant_id == tenant_id)
            .where(Ticket.status.in_([TicketStatusEnum.OPEN, TicketStatusEnum.PENDING]))
            .where(Ticket.sla_due_at.isnot(None))
            .where(Ticket.sla_due_at <= now)
            .order_by(Ticket.sla_due_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
