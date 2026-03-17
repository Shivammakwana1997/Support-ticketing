from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository with tenant-scoped CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: UUID, tenant_id: UUID | None = None) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)
        if tenant_id and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        tenant_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        filters: list[Any] | None = None,
    ) -> tuple[Sequence[ModelType], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == tenant_id)
            count_stmt = count_stmt.where(self.model.tenant_id == tenant_id)

        if filters:
            for f in filters:
                stmt = stmt.where(f)
                count_stmt = count_stmt.where(f)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.created_at.desc())

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def create(self, *, data: dict[str, Any]) -> ModelType:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(
        self,
        *,
        id: UUID,
        data: dict[str, Any],
        tenant_id: UUID | None = None,
    ) -> ModelType | None:
        instance = await self.get(id, tenant_id=tenant_id)
        if not instance:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID, tenant_id: UUID | None = None) -> bool:
        instance = await self.get(id, tenant_id=tenant_id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
