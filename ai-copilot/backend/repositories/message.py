from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.message import Message
from repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Message, session)

    async def get_by_conversation(
        self, conversation_id: UUID, tenant_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> Sequence[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.tenant_id == tenant_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_message(
        self, *, conversation_id: UUID, tenant_id: UUID, data: dict[str, Any]
    ) -> Message:
        data["conversation_id"] = conversation_id
        data["tenant_id"] = tenant_id
        return await self.create(data=data)
