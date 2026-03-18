from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, default=dict)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="customers")  # noqa: F821
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="customer")  # noqa: F821
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="customer")  # noqa: F821
