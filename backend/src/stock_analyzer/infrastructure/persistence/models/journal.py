"""Trade journal ORM models (docs/15-trade-journal.md).

Percentages are stored as percent points (``20.0000`` = +20%). ``user_id`` is added
in Phase 5b together with the users table.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.infrastructure.persistence.models.base import Base
from stock_analyzer.infrastructure.persistence.models.prediction import HOLDING_CATEGORIES_SQL

PCT = Numeric(9, 4)
PRICE = Numeric(18, 4)


class TradePlanModel(Base):
    """One holding plan: one start, one planned end, one exit; prediction locked at start."""

    __tablename__ = "trade_plans"
    __table_args__ = (
        CheckConstraint(f"category IN {HOLDING_CATEGORIES_SQL}", name="category"),
        CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name="status"),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('SUCCESS', 'PARTIAL', 'FAILURE', 'EXITED_EARLY')",
            name="outcome",
        ),
        # An active plan has no outcome or exit; a closed plan has all of them.
        CheckConstraint(
            "(status = 'ACTIVE' AND outcome IS NULL AND exit_date IS NULL AND exit_price IS NULL)"
            " OR (status = 'CLOSED' AND outcome IS NOT NULL AND exit_date IS NOT NULL"
            " AND exit_price IS NOT NULL)",
            name="closed_has_exit",
        ),
        CheckConstraint("exit_date IS NULL OR exit_date >= start_date", name="exit_after_start"),
        CheckConstraint("success_tolerance_pp >= 0", name="tolerance_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id"))
    parent_plan_id: Mapped[int | None] = mapped_column(ForeignKey("trade_plans.id"))
    category: Mapped[str] = mapped_column(String(4))
    start_date: Mapped[date] = mapped_column(Date)
    planned_end_date: Mapped[date] = mapped_column(Date)
    entry_price: Mapped[Decimal] = mapped_column(PRICE)
    # The predicted value the outcome is judged against (locked at start).
    target_pct: Mapped[Decimal] = mapped_column(PCT)
    stop_pct: Mapped[Decimal] = mapped_column(PCT)
    success_tolerance_pp: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="0.5")
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, server_default="false")
    status: Mapped[str] = mapped_column(String(8), server_default="ACTIVE")
    outcome: Mapped[str | None] = mapped_column(String(16))
    exit_date: Mapped[date | None] = mapped_column(Date)
    exit_price: Mapped[Decimal | None] = mapped_column(PRICE)
    actual_return_pct: Mapped[Decimal | None] = mapped_column(PCT)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlanDailyStatusModel(Base):
    """Daily tracking snapshot of an active plan."""

    __tablename__ = "plan_daily_status"

    plan_id: Mapped[int] = mapped_column(ForeignKey("trade_plans.id"), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close: Mapped[Decimal] = mapped_column(PRICE)
    return_pct: Mapped[Decimal] = mapped_column(PCT)
    day_number: Mapped[int] = mapped_column(Integer)
    is_target_reached: Mapped[bool] = mapped_column(Boolean)
    is_stop_hit: Mapped[bool] = mapped_column(Boolean)
