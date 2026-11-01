"""Holding categories: short-term sessions (Q75) and long-term calendar periods (docs/16)."""

import math
from decimal import Decimal
from enum import StrEnum

TRADING_DAYS_PER_YEAR = 250
CALENDAR_DAYS_PER_YEAR = 365
LONG_TERM_STOP_PCT = Decimal(-7)
SHORT_TERM_STOP_PCT = Decimal(-3)  # Q76


class HoldingCategory(StrEnum):
    """A planned holding period: short ones in trading sessions, long ones in calendar days."""

    S1 = "1D"
    S3 = "3D"
    S5 = "5D"
    S10 = "10D"
    D50 = "50D"
    D100 = "100D"
    D200 = "200D"
    D300 = "300D"
    Y1 = "1Y"
    Y2 = "2Y"
    Y3 = "3Y"

    @property
    def is_short_term(self) -> bool:
        """1 day to 2 weeks (Q75): counted in trading sessions."""
        return self in _SESSIONS

    @property
    def sessions(self) -> int | None:
        """Trading sessions of a short-term hold, ``None`` for long-term categories."""
        return _SESSIONS.get(self)

    @property
    def calendar_days(self) -> int:
        """Return the holding period in calendar days (approximate for short-term holds)."""
        sessions = _SESSIONS.get(self)
        if sessions is not None:
            return math.ceil(sessions * 7 / 5)  # five sessions a week
        return _CALENDAR_DAYS[self]

    @property
    def approx_trading_days(self) -> int:
        """Return the number of trading days (exact for short-term holds)."""
        sessions = _SESSIONS.get(self)
        if sessions is not None:
            return sessions
        return round(self.calendar_days * TRADING_DAYS_PER_YEAR / CALENDAR_DAYS_PER_YEAR)

    @property
    def default_stop_pct(self) -> Decimal:
        """Stop-loss used for labels, the baseline and default plans (Q76)."""
        return SHORT_TERM_STOP_PCT if self.is_short_term else LONG_TERM_STOP_PCT

    @property
    def shows_cagr(self) -> bool:
        """Return whether a per-year CAGR is meaningful (1 year and longer only, Q4)."""
        return self.calendar_days >= CALENDAR_DAYS_PER_YEAR


_SESSIONS = {
    HoldingCategory.S1: 1,
    HoldingCategory.S3: 3,
    HoldingCategory.S5: 5,
    HoldingCategory.S10: 10,
}
_CALENDAR_DAYS = {
    HoldingCategory.D50: 50,
    HoldingCategory.D100: 100,
    HoldingCategory.D200: 200,
    HoldingCategory.D300: 300,
    HoldingCategory.Y1: 365,
    HoldingCategory.Y2: 730,
    HoldingCategory.Y3: 1095,
}
