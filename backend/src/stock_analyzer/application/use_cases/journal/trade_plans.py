"""Trade journal use cases: start, close, list and read plans (docs/15-trade-journal.md)."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.journal.trade_plan import (
    DEFAULT_STOP_PCT,
    DEFAULT_SUCCESS_TOLERANCE_PP,
    InvalidPlanError,
    PlanOutcome,
    PlanStatus,
    TradePlan,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar


@dataclass(frozen=True, slots=True)
class CreateTradePlanRequest:
    """Input for starting a plan; omitted values are filled from the data (POC defaults)."""

    symbol: str
    category: HoldingCategory
    start_date: date
    target_pct: Decimal | None = None
    entry_price: Decimal | None = None
    stop_pct: Decimal = DEFAULT_STOP_PCT
    success_tolerance_pp: Decimal = DEFAULT_SUCCESS_TOLERANCE_PP
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
class CategoryRecord:
    """Track record of closed plans for one holding category."""

    category: HoldingCategory
    closed: int
    outcomes: dict[PlanOutcome, int]
    avg_bias_pp: Decimal | None


@dataclass(frozen=True, slots=True)
class JournalSummary:
    """Headline numbers for Home and the journal's track record.

    ``avg_bias_pp`` = average (actual - predicted) in percent points over closed plans that ran
    to an outcome (exited-early plans excluded): positive means the model was too cautious.
    """

    active: int
    closed: int
    outcomes: dict[PlanOutcome, int]
    success_rate: Decimal | None
    avg_bias_pp: Decimal | None
    by_category: list[CategoryRecord] = field(default_factory=list)


def _bias(plans: list[TradePlan]) -> Decimal | None:
    judged = [
        p
        for p in plans
        if p.actual_return_pct is not None and p.outcome is not PlanOutcome.EXITED_EARLY
    ]
    if not judged:
        return None
    total = sum(((p.actual_return_pct or Decimal(0)) - p.target_pct for p in judged), Decimal(0))
    return (total / len(judged)).quantize(Decimal("0.01"))


class TradePlanService:
    """Start, close and read journal plans."""

    def __init__(self, uow_factory: UnitOfWorkFactory, calendar: TradingCalendar) -> None:
        """Use ``calendar`` to work out planned end dates."""
        self._uow_factory = uow_factory
        self._calendar = calendar

    async def create(self, request: CreateTradePlanRequest) -> TradePlan:
        """Start a plan, locking the latest prediction for the category.

        Defaults (Q28, Q29, Q31 POC choices): entry price = the close on (or before) the
        start date; target = the predicted median for the category; both can be overridden.
        """
        async with self._uow_factory() as uow:
            stock = await uow.stocks.get_by_symbol(request.symbol)
            if stock is None or stock.id is None:
                raise NotFoundError(f"stock {request.symbol} not found")
            prediction = next(
                (
                    p
                    for p in await uow.predictions.latest_for_stock(stock.id)
                    if p.category is request.category
                ),
                None,
            )
            entry_price = request.entry_price
            if entry_price is None:
                candles = await uow.prices.get_candles(stock.id, end=request.start_date)
                if not candles:
                    raise InvalidPlanError("no price on or before the start date; enter a price")
                entry_price = candles[-1].close
            target_pct = request.target_pct
            if target_pct is None:
                if prediction is None or prediction.range.p50_pct <= 0:
                    raise InvalidPlanError("no positive predicted return; enter a target %")
                target_pct = prediction.range.p50_pct
            plan = TradePlan.start(
                stock_id=stock.id,
                category=request.category,
                start_date=request.start_date,
                planned_end_date=self._calendar.planned_end_date(
                    request.start_date, request.category
                ),
                entry_price=entry_price,
                target_pct=target_pct,
                stop_pct=request.stop_pct,
                success_tolerance_pp=request.success_tolerance_pp,
                prediction_id=prediction.id if prediction else None,
                notes=request.notes,
            )
            plan = await uow.trade_plans.add(plan)
            await uow.commit()
            return plan

    async def close(self, request: CloseTradePlanRequest) -> TradePlan:
        """Record the exit; the domain calculates the outcome."""
        async with self._uow_factory() as uow:
            plan = await uow.trade_plans.get(request.plan_id)
            if plan is None:
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

    async def get(self, plan_id: int) -> TradePlan:
        """Return one plan or raise :class:`NotFoundError`."""
        async with self._uow_factory() as uow:
            plan = await uow.trade_plans.get(plan_id)
        if plan is None:
            raise NotFoundError(f"trade plan {plan_id} not found")
        return plan

    async def summary(self) -> JournalSummary:
        """Return counts, success rate and model bias overall and per holding category."""
        plans = await self.list_all()
        closed = [p for p in plans if p.status is PlanStatus.CLOSED]
        outcomes = Counter(p.outcome for p in closed if p.outcome)
        judged = sum(n for o, n in outcomes.items() if o is not PlanOutcome.EXITED_EARLY)
        by_category = [
            CategoryRecord(
                category=category,
                closed=len(group),
                outcomes=dict(Counter(p.outcome for p in group if p.outcome)),
                avg_bias_pp=_bias(group),
            )
            for category in HoldingCategory
            if (group := [p for p in closed if p.category is category])
        ]
        return JournalSummary(
            active=len(plans) - len(closed),
            closed=len(closed),
            outcomes=dict(outcomes),
            success_rate=(
                (Decimal(outcomes[PlanOutcome.SUCCESS]) / judged).quantize(Decimal("0.0001"))
                if judged
                else None
            ),
            avg_bias_pp=_bias(closed),
            by_category=by_category,
        )

    async def list_all(self) -> list[TradePlan]:
        """Return every plan, newest first."""
        async with self._uow_factory() as uow:
            return await uow.trade_plans.list_all()
