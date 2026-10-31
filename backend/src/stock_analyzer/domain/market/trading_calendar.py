"""Trading calendar: weekends and exchange holidays are not trading days."""

from collections.abc import Iterable
from datetime import date, timedelta

from stock_analyzer.domain.market.holding_category import HoldingCategory

SATURDAY = 5


class TradingCalendar:
    """Answers "is this a trading day?" for one market."""

    def __init__(self, holidays: Iterable[date] = ()) -> None:
        """Create a calendar that skips weekends and the given ``holidays``."""
        self._holidays = frozenset(holidays)

    def is_trading_day(self, day: date) -> bool:
        """Return whether the market is open on ``day``."""
        return day.weekday() < SATURDAY and day not in self._holidays

    def next_trading_day(self, day: date) -> date:
        """Return ``day`` if it is a trading day, otherwise the next one."""
        while not self.is_trading_day(day):
            day += timedelta(days=1)
        return day

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return every trading day from ``start`` to ``end`` inclusive."""
        days, day = [], start
        while day <= end:
            if self.is_trading_day(day):
                days.append(day)
            day += timedelta(days=1)
        return days

    def planned_end_date(self, start: date, category: HoldingCategory) -> date:
        """Return the plan end: ``start`` + the category's calendar days, on a trading day."""
        return self.next_trading_day(start + timedelta(days=category.calendar_days))
