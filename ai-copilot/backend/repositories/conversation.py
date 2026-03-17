from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.conversation import Conversation
from backend.models.enums import ConversationStatusEnum
from backend.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Conversation, session)

    async def get_by_customer(
        self, customer_id: UUID, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_agent(
        self, agent_id: UUID, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.assigned_agent_id == agent_id)
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(
        self, status: ConversationStatusEnum, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.status == status)
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
