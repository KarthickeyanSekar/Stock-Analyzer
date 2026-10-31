"""Trade journal request and response models."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from stock_analyzer.domain.journal.trade_plan import (
    DEFAULT_STOP_PCT,
    DEFAULT_SUCCESS_TOLERANCE_PP,
    PlanOutcome,
    PlanStatus,
    TradePlan,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory


class CreateTradePlanBody(BaseModel):
    """Start a plan. Omit ``entry_price`` / ``target_pct`` to use the close and the prediction."""

    symbol: str = Field(examples=["RELIANCE"])
    category: HoldingCategory = Field(examples=["50D"])
    start_date: date
    entry_price: Decimal | None = Field(default=None, gt=0)
    target_pct: Decimal | None = Field(default=None, gt=0, examples=[10])
    stop_pct: Decimal = Field(default=DEFAULT_STOP_PCT, lt=0)
    success_tolerance_pp: Decimal = Field(default=DEFAULT_SUCCESS_TOLERANCE_PP, ge=0)
    notes: str | None = None


class CloseTradePlanBody(BaseModel):
    """Record the exit; the outcome is calculated by the server."""

    exit_date: date
    exit_price: Decimal = Field(gt=0)
    exited_early: bool = False
    notes: str | None = None


class TradePlanResponse(BaseModel):
    """A journal plan with its locked prediction values and outcome."""

    id: int
    symbol: str
    category: HoldingCategory
    start_date: date
    planned_end_date: date
    entry_price: float
    target_pct: float
    target_price: float
    stop_pct: float
    stop_price: float
    success_tolerance_pp: float
    prediction_id: int | None
    status: PlanStatus
    outcome: PlanOutcome | None
    exit_date: date | None
    exit_price: float | None
    actual_return_pct: float | None
    notes: str | None

    @classmethod
    def from_domain(cls, plan: TradePlan, symbol: str) -> "TradePlanResponse":
        """Map a domain plan."""
        return cls(
            id=plan.id or 0,
            symbol=symbol,
            category=plan.category,
            start_date=plan.start_date,
            planned_end_date=plan.planned_end_date,
            entry_price=float(plan.entry_price),
            target_pct=float(plan.target_pct),
            target_price=round(float(plan.target_price), 2),
            stop_pct=float(plan.stop_pct),
            stop_price=round(float(plan.stop_price), 2),
            success_tolerance_pp=float(plan.success_tolerance_pp),
            prediction_id=plan.prediction_id,
            status=plan.status,
            outcome=plan.outcome,
            exit_date=plan.exit_date,
            exit_price=float(plan.exit_price) if plan.exit_price is not None else None,
            actual_return_pct=(
                float(plan.actual_return_pct) if plan.actual_return_pct is not None else None
            ),
            notes=plan.notes,
        )
