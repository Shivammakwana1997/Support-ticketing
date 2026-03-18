from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", lazy="selectin")  # noqa: F821
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="tenant", lazy="selectin")  # noqa: F821
    customers: Mapped[list["Customer"]] = relationship("Customer", back_populates="tenant", lazy="selectin")  # noqa: F821
