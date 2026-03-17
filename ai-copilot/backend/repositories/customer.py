from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.customer import Customer
from backend.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Customer, session)

    async def get_by_email(self, email: str, tenant_id: UUID) -> Customer | None:
        stmt = (
            select(Customer)
            .where(Customer.email == email)
            .where(Customer.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str, tenant_id: UUID) -> Customer | None:
        stmt = (
            select(Customer)
            .where(Customer.external_id == external_id)
            .where(Customer.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
