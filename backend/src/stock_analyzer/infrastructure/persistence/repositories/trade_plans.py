"""SQLAlchemy trade plan repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.journal.trade_plan import (
    EntrySource,
    PlanOutcome,
    PlanStatus,
    TradePlan,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.infrastructure.persistence.models import TradePlanModel


def _to_domain(row: TradePlanModel) -> TradePlan:
    return TradePlan(
        id=row.id,
        stock_id=row.stock_id,
        category=HoldingCategory(row.category),
        start_date=row.start_date,
        planned_end_date=row.planned_end_date,
        entry_price=row.entry_price,
        target_pct=row.target_pct,
        stop_pct=row.stop_pct,
        success_tolerance_pp=row.success_tolerance_pp,
        prediction_id=row.prediction_id,
        predicted_pct=row.predicted_pct,
        reference_close=row.reference_close,
        entry_source=EntrySource(row.entry_source),
        parent_plan_id=row.parent_plan_id,
        is_trailing_stop_enabled=row.trailing_stop_enabled,
        status=PlanStatus(row.status),
        outcome=PlanOutcome(row.outcome) if row.outcome else None,
        exit_date=row.exit_date,
        exit_price=row.exit_price,
        actual_return_pct=row.actual_return_pct,
        notes=row.notes,
    )


def _apply(plan: TradePlan, row: TradePlanModel) -> None:
    row.status = plan.status.value
    row.outcome = plan.outcome.value if plan.outcome else None
    row.exit_date = plan.exit_date
    row.exit_price = plan.exit_price
    row.actual_return_pct = plan.actual_return_pct
    row.notes = plan.notes
    if plan.status is PlanStatus.CLOSED and row.closed_at is None:
        row.closed_at = datetime.now(tz=UTC)


class SqlAlchemyTradePlanRepository:
    """Trade plans in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, plan: TradePlan) -> TradePlan:
        """Store a new plan and return it with its id."""
        row = TradePlanModel(
            stock_id=plan.stock_id,
            category=plan.category.value,
            start_date=plan.start_date,
            planned_end_date=plan.planned_end_date,
            entry_price=plan.entry_price,
            target_pct=plan.target_pct,
            stop_pct=plan.stop_pct,
            success_tolerance_pp=plan.success_tolerance_pp,
            prediction_id=plan.prediction_id,
            predicted_pct=plan.predicted_pct,
            reference_close=plan.reference_close,
            entry_source=plan.entry_source.value,
            parent_plan_id=plan.parent_plan_id,
            trailing_stop_enabled=plan.is_trailing_stop_enabled,
        )
        _apply(plan, row)
        self._session.add(row)
        await self._session.flush()
        plan.id = row.id
        return plan

    async def get(self, plan_id: int) -> TradePlan | None:
        """Return one plan, or ``None``."""
        row = await self._session.get(TradePlanModel, plan_id)
        return _to_domain(row) if row else None

    async def list_all(self) -> list[TradePlan]:
        """Return every plan, newest first."""
        rows = await self._session.scalars(
            select(TradePlanModel).order_by(TradePlanModel.created_at.desc(), TradePlanModel.id)
        )
        return [_to_domain(row) for row in rows]

    async def update(self, plan: TradePlan) -> None:
        """Persist changes to an existing plan."""
        row = await self._session.get(TradePlanModel, plan.id)
        if row is None:
            raise LookupError(f"trade plan {plan.id} not found")
        _apply(plan, row)
        await self._session.flush()
