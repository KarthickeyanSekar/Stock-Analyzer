"""Trade journal use cases: start, preview, close, track and read plans (docs/15-trade-journal.md).

Decisions: Q28 calendar-day categories (end date on the next trading day), Q29 entry price =
close on the start date unless typed in (the close is kept as ``reference_close``), Q31 own
target allowed while the locked prediction is stored and used to judge the outcome.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWork, UnitOfWorkFactory
from stock_analyzer.domain.journal.progress import PlanProgress, track
from stock_analyzer.domain.journal.settings import PositionSize, suggest_position
from stock_analyzer.domain.journal.trade_plan import (
    InvalidPlanError,
    PlanOutcome,
    PlanStatus,
    TradePlan,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.prediction.prediction import Prediction

RATE_PLACES = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class CreateTradePlanRequest:
    """Input for starting a plan; omitted values come from the data and the settings."""

    symbol: str
    category: HoldingCategory
    start_date: date
    target_pct: Decimal | None = None
    entry_price: Decimal | None = None
    stop_pct: Decimal | None = None
    success_tolerance_pp: Decimal | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CloseTradePlanRequest:
    """Input for closing a plan; the outcome is calculated, never supplied."""

    plan_id: int
    exit_date: date
    exit_price: Decimal
    exited_early: bool = False
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class PlanPreview:
    """What a plan would look like if started now, before anything is saved."""

    plan: TradePlan
    position: PositionSize
    paper_capital: Decimal
    risk_pct: Decimal


@dataclass(frozen=True, slots=True)
class CategoryRecord:
    """Track record of closed plans for one holding category."""

    category: HoldingCategory
    closed: int
    outcomes: dict[PlanOutcome, int]
    success_rate: Decimal | None
    avg_bias_pp: Decimal | None


@dataclass(frozen=True, slots=True)
class JournalSummary:
    """Headline numbers for Home and the journal's track record.

    ``avg_bias_pp`` = average (actual - predicted) in percent points over closed plans that ran
    to an outcome (exited-early plans excluded): positive means the model was too cautious.
    ``own_target_hit_rate`` = share of those plans that reached your own target (Q31).
    """

    active: int
    closed: int
    outcomes: dict[PlanOutcome, int]
    success_rate: Decimal | None
    avg_bias_pp: Decimal | None
    own_target_hit_rate: Decimal | None = None
    by_category: list[CategoryRecord] = field(default_factory=list)


def _judged(plans: list[TradePlan]) -> list[TradePlan]:
    return [
        p
        for p in plans
        if p.actual_return_pct is not None and p.outcome is not PlanOutcome.EXITED_EARLY
    ]


def _rate(hits: int, total: int) -> Decimal | None:
    return (Decimal(hits) / total).quantize(RATE_PLACES) if total else None


def _bias(plans: list[TradePlan]) -> Decimal | None:
    judged = _judged(plans)
    if not judged:
        return None
    total = sum(((p.actual_return_pct or Decimal(0)) - p.benchmark_pct for p in judged), Decimal(0))
    return (total / len(judged)).quantize(Decimal("0.01"))


def _success_rate(plans: list[TradePlan]) -> Decimal | None:
    judged = _judged(plans)
    return _rate(sum(p.outcome is PlanOutcome.SUCCESS for p in judged), len(judged))


def _visible(plan: TradePlan, owner_id: UUID | None) -> bool:
    """Users only see their own plans (``None`` = a job that sees all)."""
    return owner_id is None or plan.owner_id == owner_id


class TradePlanService:
    """Start, preview, close, track and read journal plans."""

    def __init__(self, uow_factory: UnitOfWorkFactory, calendar: TradingCalendar) -> None:
        """Use ``calendar`` to work out planned end dates and trading days."""
        self._uow_factory = uow_factory
        self._calendar = calendar

    async def _draft(
        self, uow: UnitOfWork, request: CreateTradePlanRequest, owner_id: UUID | None
    ) -> TradePlan:
        """Build (but don't save) the plan the request describes."""
        stock = await uow.stocks.get_by_symbol(request.symbol)
        if stock is None or stock.id is None:
            raise NotFoundError(f"stock {request.symbol} not found")
        settings = await uow.settings.get(owner_id)
        prediction: Prediction | None = next(
            (
                p
                for p in await uow.predictions.latest_for_stock(stock.id)
                if p.category is request.category
            ),
            None,
        )
        candles = await uow.prices.get_candles(stock.id, end=request.start_date)
        reference_close = candles[-1].close if candles else None
        entry_price = request.entry_price or reference_close
        if entry_price is None:
            raise InvalidPlanError("no price on or before the start date; enter a price")
        predicted_pct = prediction.range.p50_pct if prediction else None
        target_pct = request.target_pct
        if target_pct is None:
            if predicted_pct is None or predicted_pct <= 0:
                raise InvalidPlanError("no positive predicted return; enter a target %")
            target_pct = predicted_pct
        return TradePlan.start(
            stock_id=stock.id,
            category=request.category,
            start_date=request.start_date,
            planned_end_date=self._calendar.planned_end_date(request.start_date, request.category),
            entry_price=entry_price,
            target_pct=target_pct,
            stop_pct=request.stop_pct
            if request.stop_pct is not None
            else settings.default_stop_pct,
            success_tolerance_pp=(
                request.success_tolerance_pp
                if request.success_tolerance_pp is not None
                else settings.success_tolerance_pp
            ),
            prediction_id=prediction.id if prediction else None,
            predicted_pct=predicted_pct,
            reference_close=reference_close,
            notes=request.notes,
            owner_id=owner_id,
        )

    async def preview(
        self, request: CreateTradePlanRequest, owner_id: UUID | None = None
    ) -> PlanPreview:
        """Return the plan and the suggested position size without saving anything."""
        async with self._uow_factory() as uow:
            plan = await self._draft(uow, request, owner_id)
            settings = await uow.settings.get(owner_id)
        return PlanPreview(
            plan=plan,
            position=suggest_position(
                settings.paper_capital, settings.risk_pct, plan.stop_pct, plan.entry_price
            ),
            paper_capital=settings.paper_capital,
            risk_pct=settings.risk_pct,
        )

    async def create(
        self, request: CreateTradePlanRequest, owner_id: UUID | None = None
    ) -> TradePlan:
        """Start a plan, locking the latest prediction and the current settings."""
        async with self._uow_factory() as uow:
            plan = await uow.trade_plans.add(await self._draft(uow, request, owner_id))
            await uow.commit()
            return plan

    async def close(
        self, request: CloseTradePlanRequest, owner_id: UUID | None = None
    ) -> TradePlan:
        """Record the exit; the domain calculates the outcome."""
        async with self._uow_factory() as uow:
            plan = await uow.trade_plans.get(request.plan_id)
            if plan is None or not _visible(plan, owner_id):
                raise NotFoundError(f"trade plan {request.plan_id} not found")
            plan.close(
                request.exit_date,
                request.exit_price,
                exited_early=request.exited_early,
                notes=request.notes,
            )
            await uow.trade_plans.update(plan)
            await uow.commit()
            return plan

    async def get(self, plan_id: int, owner_id: UUID | None = None) -> TradePlan:
        """Return one plan or raise :class:`NotFoundError`."""
        async with self._uow_factory() as uow:
            plan = await uow.trade_plans.get(plan_id)
        if plan is None or not _visible(plan, owner_id):
            raise NotFoundError(f"trade plan {plan_id} not found")
        return plan

    async def progress(
        self, plans: list[TradePlan], as_of: date | None = None
    ) -> dict[int, PlanProgress]:
        """Return today's progress (or on ``as_of``) for every active plan with prices."""
        found: dict[int, PlanProgress] = {}
        async with self._uow_factory() as uow:
            for plan in plans:
                if plan.status is not PlanStatus.ACTIVE or plan.id is None:
                    continue
                candles = await uow.prices.get_candles(plan.stock_id, plan.start_date, as_of)
                if candles and (result := track(plan, candles, self._calendar, as_of or date.max)):
                    found[plan.id] = result
        return found

    async def summary(self, owner_id: UUID | None = None) -> JournalSummary:
        """Return counts, success rates and model bias overall and per holding category."""
        plans = await self.list_all(owner_id)
        closed = [p for p in plans if p.status is PlanStatus.CLOSED]
        judged = _judged(closed)
        return JournalSummary(
            active=len(plans) - len(closed),
            closed=len(closed),
            outcomes=dict(Counter(p.outcome for p in closed if p.outcome)),
            success_rate=_success_rate(closed),
            avg_bias_pp=_bias(closed),
            own_target_hit_rate=_rate(sum(bool(p.is_own_target_met) for p in judged), len(judged)),
            by_category=[
                CategoryRecord(
                    category=category,
                    closed=len(group),
                    outcomes=dict(Counter(p.outcome for p in group if p.outcome)),
                    success_rate=_success_rate(group),
                    avg_bias_pp=_bias(group),
                )
                for category in HoldingCategory
                if (group := [p for p in closed if p.category is category])
            ],
        )

    async def list_all(self, owner_id: UUID | None = None) -> list[TradePlan]:
        """Return the owner's plans (every plan for jobs: ``None``), newest first."""
        async with self._uow_factory() as uow:
            return await uow.trade_plans.list_all(owner_id)
