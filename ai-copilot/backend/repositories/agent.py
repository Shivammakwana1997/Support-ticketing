from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.agent import Agent
from backend.models.enums import AgentStatusEnum
from backend.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Agent, session)

    async def get_available_agents(self, tenant_id: UUID) -> Sequence[Agent]:
        stmt = (
            select(Agent)
            .where(Agent.tenant_id == tenant_id)
            .where(Agent.status == AgentStatusEnum.AVAILABLE)
            .order_by(Agent.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_tenant(
        self, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[Agent]:
        stmt = (
            select(Agent)
            .where(Agent.tenant_id == tenant_id)
            .order_by(Agent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: UUID) -> Agent | None:
        stmt = select(Agent).where(Agent.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
