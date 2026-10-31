"""Data provider configuration ORM models (docs/22-provider-configuration-ui.md)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.infrastructure.persistence.models.base import Base


class ProviderModel(Base):
    """A configured provider plugin instance (e.g., ``mock``, later ``eodhd``)."""

    __tablename__ = "providers"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('MARKET_DATA', 'FUNDAMENTALS', 'MACRO', 'NOTIFY', 'LLM')", name="kind"
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    plugin_name: Mapped[str] = mapped_column(String(32), unique=True)
    kind: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(100))
    is_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderCredentialModel(Base):
    """One encrypted credential field of a provider (Fernet, key ``SA_MASTER_KEY``)."""

    __tablename__ = "provider_credentials"

    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), primary_key=True)
    field: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    # Last 4 characters, for masked display only (never the full value).
    last4: Mapped[str] = mapped_column(String(4))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderAssignmentModel(Base):
    """Which provider serves a data type in a market, in failover order (1 = primary)."""

    __tablename__ = "provider_assignments"
    __table_args__ = (
        UniqueConstraint("market_code", "data_type", "provider_id"),
        CheckConstraint("priority >= 1", name="priority_positive"),
    )

    market_code: Mapped[str] = mapped_column(ForeignKey("markets.code"), primary_key=True)
    data_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
