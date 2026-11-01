"""Trade journal request and response models."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from stock_analyzer.application.use_cases.journal.trade_plans import JournalSummary, PlanPreview
from stock_analyzer.domain.journal.progress import PlanProgress
from stock_analyzer.domain.journal.settings import MAX_RISK_PCT, MAX_TOLERANCE_PP, JournalSettings
from stock_analyzer.domain.journal.trade_plan import (
    EntrySource,
    PlanOutcome,
    PlanStatus,
    TradePlan,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _price(value: Decimal) -> float:
    return round(float(value), 2)


class CreateTradePlanBody(BaseModel):
    """Start a plan. Omitted values come from the close, the prediction and the settings."""

    symbol: str = Field(examples=["RELIANCE"])
    category: HoldingCategory = Field(examples=["50D"])
    start_date: date
    entry_price: Decimal | None = Field(
        default=None, gt=0, description="Your actual buy price; default: the close (Q29)"
    )
    target_pct: Decimal | None = Field(
        default=None, gt=0, examples=[10], description="Your own target; default: prediction"
    )
    stop_pct: Decimal | None = Field(default=None, lt=0, description="Default: settings")
    success_tolerance_pp: Decimal | None = Field(
        default=None, ge=0, description="Default: settings"
    )
    notes: str | None = None


class CloseTradePlanBody(BaseModel):
    """Record the exit; the outcome is calculated by the server."""

    exit_date: date
    exit_price: Decimal = Field(gt=0)
    exited_early: bool = False
    notes: str | None = None


PROGRESS_EXAMPLE: dict[str, JsonValue] = {
    "as_of": "2026-10-30",
    "day_number": 12,
    "total_days": 251,
    "last_close": 3012.4,
    "return_pct": 2.11,
    "progress_pct": 51.6,
    "target_reached_on": None,
    "stop_hit_on": None,
    "is_target_reached": False,
    "is_stop_hit": False,
    "is_end_date_reached": False,
}


class PlanProgressResponse(BaseModel):
    """Where an active plan stands on the last trading day with a price."""

    model_config = ConfigDict(json_schema_extra={"examples": [PROGRESS_EXAMPLE]})

    as_of: date
    day_number: int = Field(description="Trading days since the start (start day = 0)")
    total_days: int = Field(description="Trading days from the start to the planned end")
    last_close: float
    return_pct: float
    progress_pct: float = Field(description="0 = stop price, 100 = target price (clamped)")
    target_reached_on: date | None
    stop_hit_on: date | None
    is_target_reached: bool
    is_stop_hit: bool
    is_end_date_reached: bool

    @classmethod
    def from_domain(cls, progress: PlanProgress) -> "PlanProgressResponse":
        """Map a domain progress snapshot."""
        return cls(
            as_of=progress.as_of,
            day_number=progress.day_number,
            total_days=progress.total_days,
            last_close=float(progress.last_close),
            return_pct=float(progress.return_pct),
            progress_pct=float(progress.progress_pct),
            target_reached_on=progress.target_reached_on,
            stop_hit_on=progress.stop_hit_on,
            is_target_reached=progress.is_target_reached,
            is_stop_hit=progress.is_stop_hit,
            is_end_date_reached=progress.is_end_date_reached,
        )


class TradePlanResponse(BaseModel):
    """A journal plan with its locked values, progress (active) and outcome (closed)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "symbol": "RELIANCE",
                    "category": "1Y",
                    "start_date": "2026-10-30",
                    "planned_end_date": "2027-11-01",
                    "entry_price": 2950.0,
                    "reference_close": 2950.0,
                    "entry_source": "CLOSE",
                    "target_pct": 12.0,
                    "predicted_pct": 10.49,
                    "benchmark_pct": 10.49,
                    "benchmark_price": 3259.46,
                    "target_price": 3304.0,
                    "stop_pct": -7.0,
                    "stop_price": 2743.5,
                    "success_tolerance_pp": 0.5,
                    "prediction_id": 42,
                    "status": "CLOSED",
                    "outcome": "SUCCESS",
                    "exit_date": "2027-11-01",
                    "exit_price": 3265.65,
                    "actual_return_pct": 10.7,
                    "own_target_gap_pp": -1.3,
                    "is_own_target_met": False,
                    "progress": None,
                    "notes": None,
                }
            ]
        }
    )

    id: int
    symbol: str
    category: HoldingCategory
    start_date: date
    planned_end_date: date
    entry_price: float
    reference_close: float | None = Field(description="Provider close on the start date (Q29)")
    entry_source: EntrySource
    target_pct: float = Field(description="Your target; drives the target/stop prices (Q31)")
    predicted_pct: float | None = Field(description="Locked predicted median (Q31)")
    benchmark_pct: float = Field(description="What the outcome is judged against")
    benchmark_price: float = Field(description="Price at which the return equals the benchmark")
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
    own_target_gap_pp: float | None = Field(description="Actual minus your own target")
    is_own_target_met: bool | None
    progress: PlanProgressResponse | None
    notes: str | None

    @classmethod
    def from_domain(
        cls, plan: TradePlan, symbol: str, progress: PlanProgress | None = None
    ) -> "TradePlanResponse":
        """Map a domain plan and, for active plans, its progress."""
        return cls(
            id=plan.id or 0,
            symbol=symbol,
            category=plan.category,
            start_date=plan.start_date,
            planned_end_date=plan.planned_end_date,
            entry_price=float(plan.entry_price),
            reference_close=_num(plan.reference_close),
            entry_source=plan.entry_source,
            target_pct=float(plan.target_pct),
            predicted_pct=_num(plan.predicted_pct),
            benchmark_pct=float(plan.benchmark_pct),
            benchmark_price=_price(plan.benchmark_price),
            target_price=_price(plan.target_price),
            stop_pct=float(plan.stop_pct),
            stop_price=_price(plan.stop_price),
            success_tolerance_pp=float(plan.success_tolerance_pp),
            prediction_id=plan.prediction_id,
            status=plan.status,
            outcome=plan.outcome,
            exit_date=plan.exit_date,
            exit_price=_num(plan.exit_price),
            actual_return_pct=_num(plan.actual_return_pct),
            own_target_gap_pp=_num(plan.own_target_gap_pp),
            is_own_target_met=plan.is_own_target_met,
            progress=PlanProgressResponse.from_domain(progress) if progress else None,
            notes=plan.notes,
        )


class PlanPreviewResponse(BaseModel):
    """A plan as it would start now, plus the suggested position size (nothing is saved)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "symbol": "RELIANCE",
                    "category": "1Y",
                    "start_date": "2026-10-30",
                    "planned_end_date": "2027-11-01",
                    "entry_price": 2950.0,
                    "reference_close": 2950.0,
                    "entry_source": "CLOSE",
                    "target_pct": 10.49,
                    "predicted_pct": 10.49,
                    "target_price": 3259.46,
                    "stop_pct": -7.0,
                    "stop_price": 2743.5,
                    "success_tolerance_pp": 0.5,
                    "paper_capital": 1000000.0,
                    "risk_pct": 1.0,
                    "risk_amount": 10000.0,
                    "suggested_amount": 141600.0,
                    "suggested_quantity": 48,
                }
            ]
        }
    )

    symbol: str
    category: HoldingCategory
    start_date: date
    planned_end_date: date
    entry_price: float
    reference_close: float | None
    entry_source: EntrySource
    target_pct: float
    predicted_pct: float | None
    target_price: float
    stop_pct: float
    stop_price: float
    success_tolerance_pp: float
    paper_capital: float
    risk_pct: float
    risk_amount: float = Field(description="Loss if the stop is hit: capital x risk %")
    suggested_amount: float = Field(description="Whole shares x entry price")
    suggested_quantity: int

    @classmethod
    def from_domain(cls, preview: PlanPreview, symbol: str) -> "PlanPreviewResponse":
        """Map a plan preview."""
        plan = preview.plan
        return cls(
            symbol=symbol,
            category=plan.category,
            start_date=plan.start_date,
            planned_end_date=plan.planned_end_date,
            entry_price=float(plan.entry_price),
            reference_close=_num(plan.reference_close),
            entry_source=plan.entry_source,
            target_pct=float(plan.target_pct),
            predicted_pct=_num(plan.predicted_pct),
            target_price=_price(plan.target_price),
            stop_pct=float(plan.stop_pct),
            stop_price=_price(plan.stop_price),
            success_tolerance_pp=float(plan.success_tolerance_pp),
            paper_capital=float(preview.paper_capital),
            risk_pct=float(preview.risk_pct),
            risk_amount=float(preview.position.risk_amount),
            suggested_amount=float(preview.position.amount),
            suggested_quantity=preview.position.quantity,
        )


def _counts(outcomes: dict[PlanOutcome, int]) -> dict[str, int]:
    return {outcome.value: outcomes.get(outcome, 0) for outcome in PlanOutcome}


COUNTS_EXAMPLE: dict[str, JsonValue] = {"SUCCESS": 1, "PARTIAL": 1, "FAILURE": 0, "EXITED_EARLY": 0}


class CategoryRecordResponse(BaseModel):
    """Track record for one holding category."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": "1Y",
                    "closed": 2,
                    "outcomes": COUNTS_EXAMPLE,
                    "success_rate": 0.5,
                    "avg_bias_pp": 2.61,
                }
            ]
        }
    )

    category: HoldingCategory
    closed: int
    outcomes: dict[str, int]
    success_rate: float | None
    avg_bias_pp: float | None


class JournalSummaryResponse(BaseModel):
    """Journal headline numbers; ``avg_bias_pp`` > 0 means the model was too cautious."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "active": 0,
                    "closed": 2,
                    "outcomes": COUNTS_EXAMPLE,
                    "success_rate": 0.5,
                    "avg_bias_pp": 2.61,
                    "own_target_hit_rate": 0.5,
                    "by_category": [
                        {
                            "category": "1Y",
                            "closed": 2,
                            "outcomes": COUNTS_EXAMPLE,
                            "success_rate": 0.5,
                            "avg_bias_pp": 2.61,
                        }
                    ],
                }
            ]
        }
    )

    active: int
    closed: int
    outcomes: dict[str, int]
    success_rate: float | None
    avg_bias_pp: float | None
    own_target_hit_rate: float | None = Field(description="Share that reached your own target")
    by_category: list[CategoryRecordResponse]

    @classmethod
    def from_domain(cls, summary: JournalSummary) -> "JournalSummaryResponse":
        """Map the journal summary."""
        return cls(
            active=summary.active,
            closed=summary.closed,
            outcomes=_counts(summary.outcomes),
            success_rate=_num(summary.success_rate),
            avg_bias_pp=_num(summary.avg_bias_pp),
            own_target_hit_rate=_num(summary.own_target_hit_rate),
            by_category=[
                CategoryRecordResponse(
                    category=r.category,
                    closed=r.closed,
                    outcomes=_counts(r.outcomes),
                    success_rate=_num(r.success_rate),
                    avg_bias_pp=_num(r.avg_bias_pp),
                )
                for r in summary.by_category
            ],
        )


class JournalSettingsBody(BaseModel):
    """Defaults for new plans (plans already started keep their own values)."""

    paper_capital: Decimal = Field(gt=0, examples=[1000000])
    risk_pct: Decimal = Field(gt=0, le=MAX_RISK_PCT, examples=[1])
    success_tolerance_pp: Decimal = Field(ge=0, le=MAX_TOLERANCE_PP, examples=[0.5])
    default_stop_pct: Decimal = Field(lt=0, examples=[-7])

    def to_domain(self) -> JournalSettings:
        """Build the domain settings."""
        return JournalSettings(**self.model_dump())


class JournalSettingsResponse(BaseModel):
    """The app-wide journal settings (Q63)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "paper_capital": 1000000.0,
                    "risk_pct": 1.0,
                    "success_tolerance_pp": 0.5,
                    "default_stop_pct": -7.0,
                }
            ]
        }
    )

    paper_capital: float
    risk_pct: float
    success_tolerance_pp: float
    default_stop_pct: float

    @classmethod
    def from_domain(cls, settings: JournalSettings) -> "JournalSettingsResponse":
        """Map the domain settings."""
        return cls(
            paper_capital=float(settings.paper_capital),
            risk_pct=float(settings.risk_pct),
            success_tolerance_pp=float(settings.success_tolerance_pp),
            default_stop_pct=float(settings.default_stop_pct),
        )
