"""Daily progress of an active plan from end-of-day candles (D2.2, D2.3).

Tracking only reports: it never closes a plan. The exit stays a manual journal entry.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.shared.percent import return_pct, round_pct


@dataclass(frozen=True, slots=True)
class PlanProgress:
    """Where a plan stands on ``as_of`` (only candles up to that day are used)."""

    as_of: date
    day_number: int  # trading days since the start date (start day = 0)
    total_days: int  # trading days from the start to the planned end date
    last_close: Decimal
    return_pct: Decimal
    progress_pct: Decimal  # 0 = stop price, 100 = target price (clamped)
    target_reached_on: date | None  # first day the high reached the target price
    stop_hit_on: date | None  # first day the low touched the stop price
    is_end_date_reached: bool

    @property
    def is_target_reached(self) -> bool:
        """Whether the target price has been touched since the start."""
        return self.target_reached_on is not None

    @property
    def is_stop_hit(self) -> bool:
        """Whether the stop-loss price has been touched since the start."""
        return self.stop_hit_on is not None


def progress_between_stop_and_target(plan: TradePlan, price: Decimal) -> Decimal:
    """Position of ``price`` between the stop (0) and the target (100), clamped."""
    span = plan.target_price - plan.stop_price
    if span <= 0:
        return Decimal(0)
    position = (price - plan.stop_price) / span * 100
    return round_pct(min(Decimal(100), max(Decimal(0), position)))


def _sessions_after(calendar: TradingCalendar, start: date, end: date) -> int:
    """Trading days after ``start`` up to and including ``end``."""
    return sum(1 for day in calendar.trading_days(start, end) if day > start)


def track(
    plan: TradePlan, candles: Sequence[Candle], calendar: TradingCalendar, as_of: date
) -> PlanProgress | None:
    """Return the plan's progress on ``as_of``, or ``None`` if there is no price yet.

    Progress stops at the planned end date (the time stop): later prices don't belong to it.
    """
    until = min(as_of, plan.planned_end_date)
    window = [c for c in candles if plan.start_date <= c.trade_date <= until]
    if not window:
        return None
    last = window[-1]
    # The start day's own range happened before/around the entry, so flags start the day after.
    after_start = [c for c in window if c.trade_date > plan.start_date]
    target_day = next((c.trade_date for c in after_start if c.high >= plan.target_price), None)
    stop_day = next((c.trade_date for c in after_start if c.low <= plan.stop_price), None)
    total_days = _sessions_after(calendar, plan.start_date, plan.planned_end_date)
    day_number = _sessions_after(calendar, plan.start_date, last.trade_date)
    return PlanProgress(
        as_of=last.trade_date,
        day_number=min(day_number, total_days),
        total_days=total_days,
        last_close=last.close,
        return_pct=return_pct(plan.entry_price, last.close),
        progress_pct=progress_between_stop_and_target(plan, last.close),
        target_reached_on=target_day,
        stop_hit_on=stop_day,
        is_end_date_reached=last.trade_date >= plan.planned_end_date,
    )
