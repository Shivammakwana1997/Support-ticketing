from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base
from backend.models.enums import ChannelEnum, ConversationStatusEnum


class Conversation(Base):
    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[ChannelEnum] = mapped_column(nullable=False)
    status: Mapped[ConversationStatusEnum] = mapped_column(
        default=ConversationStatusEnum.OPEN, nullable=False
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, default=dict)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")  # noqa: F821
    assigned_agent: Mapped["Agent | None"] = relationship("Agent", foreign_keys=[assigned_agent_id])  # noqa: F821
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", order_by="Message.created_at")  # noqa: F821
