from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import TicketStatusEnum, PriorityEnum, TicketCategoryEnum


class Ticket(Base):
    __tablename__ = "tickets"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TicketStatusEnum] = mapped_column(
        default=TicketStatusEnum.OPEN, nullable=False
    )
    priority: Mapped[PriorityEnum] = mapped_column(
        default=PriorityEnum.MEDIUM, nullable=False
    )
    category: Mapped[TicketCategoryEnum] = mapped_column(
        default=TicketCategoryEnum.GENERAL, nullable=False
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_breach_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, default=dict)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")  # noqa: F821
    conversation: Mapped["Conversation | None"] = relationship("Conversation")  # noqa: F821
    assigned_agent: Mapped["Agent | None"] = relationship("Agent", foreign_keys=[assigned_agent_id])  # noqa: F821
