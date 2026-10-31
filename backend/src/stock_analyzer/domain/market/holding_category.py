"""Holding categories offered by the long-term engine (docs/16-holding-period-screener.md)."""

from enum import StrEnum

TRADING_DAYS_PER_YEAR = 250
CALENDAR_DAYS_PER_YEAR = 365


class HoldingCategory(StrEnum):
    """A planned holding period, entered by users in calendar days."""

    D50 = "50D"
    D100 = "100D"
    D200 = "200D"
    D300 = "300D"
    Y1 = "1Y"
    Y2 = "2Y"
    Y3 = "3Y"

    @property
    def calendar_days(self) -> int:
        """Return the holding period in calendar days."""
        return _CALENDAR_DAYS[self]

    @property
    def approx_trading_days(self) -> int:
        """Return the approximate number of trading days (used by statistical models)."""
        return round(self.calendar_days * TRADING_DAYS_PER_YEAR / CALENDAR_DAYS_PER_YEAR)

    @property
    def shows_cagr(self) -> bool:
        """Return whether a per-year CAGR is meaningful (1 year and longer only, Q4)."""
        return self.calendar_days >= CALENDAR_DAYS_PER_YEAR


_CALENDAR_DAYS = {
    HoldingCategory.D50: 50,
    HoldingCategory.D100: 100,
    HoldingCategory.D200: 200,
    HoldingCategory.D300: 300,
    HoldingCategory.Y1: 365,
    HoldingCategory.Y2: 730,
    HoldingCategory.Y3: 1095,
}
