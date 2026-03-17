from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base
from backend.models.enums import AgentStatusEnum


class Agent(Base):
    __tablename__ = "agents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgentStatusEnum] = mapped_column(
        default=AgentStatusEnum.OFFLINE, nullable=False
    )
    skills: Mapped[list[str] | None] = mapped_column(JSON, default=list)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="agents")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="agent_profile")  # noqa: F821
