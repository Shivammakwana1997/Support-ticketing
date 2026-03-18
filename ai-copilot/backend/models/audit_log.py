from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    # Override updated_at — audit logs are immutable
    updated_at: Mapped[datetime] = mapped_column(  # type: ignore[assignment]
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    ip: Mapped[str | None] = mapped_column(String(45))
