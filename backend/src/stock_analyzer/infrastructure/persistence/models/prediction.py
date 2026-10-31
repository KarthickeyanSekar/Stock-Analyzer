"""Model version and prediction ORM models.

Percentages are stored as percent points (``20.0000`` = +20%).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.infrastructure.persistence.models.base import Base

PCT = Numeric(9, 4)
HOLDING_CATEGORIES_SQL = "('50D', '100D', '200D', '300D', '1Y', '2Y', '3Y', '5Y')"


class ModelVersionModel(Base):
    """A trained (or rule-based) model; exactly one ACTIVE version per category is used."""

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("name", "category"),
        CheckConstraint("status IN ('CANDIDATE', 'ACTIVE', 'RETIRED')", name="status"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    # NULL = one model for every category (e.g., the empirical baseline).
    category: Mapped[str | None] = mapped_column(String(4))
    algorithm: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PredictionModel(Base):
    """Predicted return range and target probabilities for one stock, date and category."""

    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint("stock_id", "as_of", "category", "model_version_id"),
        CheckConstraint(f"category IN {HOLDING_CATEGORIES_SQL}", name="category"),
        CheckConstraint("p10_pct <= p50_pct AND p50_pct <= p90_pct", name="ordered_quantiles"),
        Index(None, "stock_id", "as_of"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    as_of: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(4))
    p10_pct: Mapped[Decimal] = mapped_column(PCT)
    p50_pct: Mapped[Decimal] = mapped_column(PCT)
    p90_pct: Mapped[Decimal] = mapped_column(PCT)
    prob_up: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    # {"5": 0.71, "10": 0.55, ..., "50": 0.04}: probability of reaching +N% before the stop.
    prob_hit: Mapped[dict[str, Any]] = mapped_column(JSONB)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
