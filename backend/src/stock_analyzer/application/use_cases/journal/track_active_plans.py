"""Daily tracking job (``make track``): one progress snapshot per active plan per trading day."""

from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.journal.progress import PlanProgress, track
from stock_analyzer.domain.journal.trade_plan import PlanStatus
from stock_analyzer.domain.market.trading_calendar import TradingCalendar


class TrackActivePlans:
    """Idempotent: re-running replaces snapshots. Never changes a plan's status."""

    def __init__(self, uow_factory: UnitOfWorkFactory, calendar: TradingCalendar) -> None:
        """Track plans with fresh units of work."""
        self._uow_factory = uow_factory
        self._calendar = calendar

    async def execute(self) -> int:
        """Write snapshots for every day each active plan has prices; return how many."""
        async with self._uow_factory() as uow:
            plans = [p for p in await uow.trade_plans.list_all() if p.status is PlanStatus.ACTIVE]

        total = 0
        for plan in plans:
            if plan.id is None:  # pragma: no cover - stored plans always have ids
                continue
            async with self._uow_factory() as uow:
                # Snapshots stop at the planned end date, like the progress itself.
                candles = await uow.prices.get_candles(
                    plan.stock_id, plan.start_date, plan.planned_end_date
                )
                # Each day sees only the candles up to that day (no future data).
                snapshots: list[PlanProgress] = [
                    progress
                    for candle in candles
                    if (progress := track(plan, candles, self._calendar, candle.trade_date))
                ]
                total += await uow.plan_statuses.upsert_many(plan.id, snapshots)
                await uow.commit()
        return total
