from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.api_key import APIKey
from backend.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(APIKey, session)

    async def get_by_hash(self, key_hash: str) -> APIKey | None:
        stmt = select(APIKey).where(APIKey.key_hash == key_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_key(
        self,
        *,
        tenant_id: UUID,
        name: str,
        key_hash: str,
        scopes: list[str] | None = None,
        expires_at: Any | None = None,
    ) -> APIKey:
        return await self.create(
            data={
                "tenant_id": tenant_id,
                "name": name,
                "key_hash": key_hash,
                "scopes": scopes or [],
                "expires_at": expires_at,
            }
        )
