"""Trade plan aggregate and its outcome rules (docs/15-trade-journal.md).

One plan = one start, one planned end, one exit. The prediction is locked at start and
the outcome is calculated, never chosen: equal to the prediction within the tolerance is
SUCCESS, above is PARTIAL (the model needs tuning), below is FAILURE.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.shared.errors import DomainError
from stock_analyzer.domain.shared.percent import return_pct

DEFAULT_SUCCESS_TOLERANCE_PP = Decimal("0.5")
DEFAULT_STOP_PCT = Decimal("-7")


class PlanStatus(StrEnum):
    """Lifecycle state of a plan."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class PlanOutcome(StrEnum):
    """Calculated result of a closed plan."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"
    EXITED_EARLY = "EXITED_EARLY"


class InvalidPlanError(DomainError):
    """Raised when a plan is created with invalid values."""


class PlanAlreadyClosedError(DomainError):
    """Raised when closing a plan that is already closed."""


class InvalidExitDateError(DomainError):
    """Raised when the exit date is before the start date."""


def evaluate_outcome(
    actual_pct: Decimal, predicted_pct: Decimal, tolerance_pp: Decimal
) -> PlanOutcome:
    """Compare the actual return with the locked prediction.

    Example with a +10% prediction and ±0.5 pp: 9.5 to 10.5 → SUCCESS, 10.6 → PARTIAL,
    9.4 → FAILURE.
    """
    if abs(actual_pct - predicted_pct) <= tolerance_pp:
        return PlanOutcome.SUCCESS
    if actual_pct > predicted_pct:
        return PlanOutcome.PARTIAL
    return PlanOutcome.FAILURE


@dataclass(slots=True)
class TradePlan:
    """A manually tracked holding plan; create with :meth:`start`."""

    stock_id: int
    category: HoldingCategory
    start_date: date
    planned_end_date: date
    entry_price: Decimal
    target_pct: Decimal
    stop_pct: Decimal
    success_tolerance_pp: Decimal
    prediction_id: int | None = None
    parent_plan_id: int | None = None
    is_trailing_stop_enabled: bool = False
    status: PlanStatus = PlanStatus.ACTIVE
    outcome: PlanOutcome | None = None
    exit_date: date | None = None
    exit_price: Decimal | None = None
    actual_return_pct: Decimal | None = None
    notes: str | None = None
    id: int | None = None

    @classmethod
    def start(  # noqa: PLR0913 - a plan genuinely has this many independent inputs
        cls,
        *,
        stock_id: int,
        category: HoldingCategory,
        start_date: date,
        planned_end_date: date,
        entry_price: Decimal,
        target_pct: Decimal,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        success_tolerance_pp: Decimal = DEFAULT_SUCCESS_TOLERANCE_PP,
        prediction_id: int | None = None,
        parent_plan_id: int | None = None,
        notes: str | None = None,
    ) -> "TradePlan":
        """Start a plan; the target and tolerance are locked from this moment."""
        if entry_price <= 0:
            raise InvalidPlanError("entry price must be positive")
        if target_pct <= 0:
            raise InvalidPlanError("target % must be positive")
        if stop_pct >= 0:
            raise InvalidPlanError("stop-loss % must be negative")
        if success_tolerance_pp < 0:
            raise InvalidPlanError("success tolerance must not be negative")
        if planned_end_date <= start_date:
            raise InvalidPlanError("planned end date must be after the start date")
        return cls(
            stock_id=stock_id,
            category=category,
            start_date=start_date,
            planned_end_date=planned_end_date,
            entry_price=entry_price,
            target_pct=target_pct,
            stop_pct=stop_pct,
            success_tolerance_pp=success_tolerance_pp,
            prediction_id=prediction_id,
            parent_plan_id=parent_plan_id,
            notes=notes,
        )

    @property
    def target_price(self) -> Decimal:
        """Return the price at which the target is reached."""
        return self.entry_price * (1 + self.target_pct / 100)

    @property
    def stop_price(self) -> Decimal:
        """Return the stop-loss price."""
        return self.entry_price * (1 + self.stop_pct / 100)

    def close(
        self,
        exit_date: date,
        exit_price: Decimal,
        *,
        exited_early: bool = False,
        notes: str | None = None,
    ) -> PlanOutcome:
        """Record the exit and calculate the outcome (it can't be chosen or overridden)."""
        if self.status is PlanStatus.CLOSED:
            raise PlanAlreadyClosedError(f"plan {self.id} is already closed")
        if exit_date < self.start_date:
            raise InvalidExitDateError(f"exit {exit_date} is before start {self.start_date}")
        if exit_price <= 0:
            raise InvalidPlanError("exit price must be positive")
        self.actual_return_pct = return_pct(self.entry_price, exit_price)
        self.outcome = (
            PlanOutcome.EXITED_EARLY
            if exited_early
            else evaluate_outcome(
                self.actual_return_pct, self.target_pct, self.success_tolerance_pp
            )
        )
        self.exit_date, self.exit_price, self.status = exit_date, exit_price, PlanStatus.CLOSED
        if notes:
            self.notes = notes
        return self.outcome
