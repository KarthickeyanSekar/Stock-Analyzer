"""Fundamentals and corporate-action ORM models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.infrastructure.persistence.models.base import Base


class FundamentalsModel(Base):
    """Financial statements and ratios for one reporting period of a stock.

    ``announced_date`` is when the numbers became public; models may only use a row
    on or after that date (point-in-time, docs/26-ml-pipeline.md).
    """

    __tablename__ = "fundamentals"
    __table_args__ = (CheckConstraint("period_type IN ('Q', 'FY')", name="period_type"),)

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    period_end: Mapped[date] = mapped_column(Date, primary_key=True)
    period_type: Mapped[str] = mapped_column(String(2), primary_key=True)
    announced_date: Mapped[date | None] = mapped_column(Date)
    statements: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ratios: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_provider: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CorporateActionModel(Base):
    """A split, bonus or dividend that adjusts historical prices."""

    __tablename__ = "corporate_actions"
    __table_args__ = (
        UniqueConstraint("stock_id", "ex_date", "action_type"),
        CheckConstraint("action_type IN ('SPLIT', 'BONUS', 'DIVIDEND')", name="action_type"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    ex_date: Mapped[date] = mapped_column(Date)
    action_type: Mapped[str] = mapped_column(String(16))
    # Ratio `from:to` for splits/bonuses (e.g., 1:2); `amount` per share for dividends.
    ratio_from: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    ratio_to: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    source_provider: Mapped[str] = mapped_column(String(32))
