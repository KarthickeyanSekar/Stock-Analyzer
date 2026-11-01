"""Journal settings and position sizing (D2.4, Q63: one app-wide record until user accounts)."""

from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from stock_analyzer.domain.journal.trade_plan import (
    DEFAULT_STOP_PCT,
    DEFAULT_SUCCESS_TOLERANCE_PP,
    InvalidPlanError,
)

DEFAULT_PAPER_CAPITAL = Decimal("1000000")
DEFAULT_RISK_PCT = Decimal("1")
MAX_RISK_PCT = Decimal("10")
MAX_TOLERANCE_PP = Decimal("10")
PAISE = Decimal("0.01")


class InvalidSettingsError(InvalidPlanError):
    """Raised when settings are out of range."""


@dataclass(frozen=True, slots=True)
class JournalSettings:
    """Defaults for new plans; plans copy them at start, so later edits never change a plan."""

    paper_capital: Decimal = DEFAULT_PAPER_CAPITAL
    risk_pct: Decimal = DEFAULT_RISK_PCT
    success_tolerance_pp: Decimal = DEFAULT_SUCCESS_TOLERANCE_PP
    default_stop_pct: Decimal = DEFAULT_STOP_PCT

    def __post_init__(self) -> None:
        """Reject values that make no sense for a paper portfolio."""
        if self.paper_capital <= 0:
            raise InvalidSettingsError("paper capital must be positive")
        if not Decimal(0) < self.risk_pct <= MAX_RISK_PCT:
            raise InvalidSettingsError(f"risk % must be above 0 and at most {MAX_RISK_PCT}")
        if not Decimal(0) <= self.success_tolerance_pp <= MAX_TOLERANCE_PP:
            raise InvalidSettingsError(f"tolerance must be 0 to {MAX_TOLERANCE_PP} pp")
        if self.default_stop_pct >= 0:
            raise InvalidSettingsError("default stop-loss % must be negative")


@dataclass(frozen=True, slots=True)
class PositionSize:
    """How much to put into one plan so a stop-out loses ``risk_pct`` of the capital."""

    amount: Decimal
    quantity: int
    risk_amount: Decimal


def suggest_position(
    capital: Decimal, risk_pct: Decimal, stop_pct: Decimal, entry_price: Decimal
) -> PositionSize:
    """Amount = capital x risk % / |stop %|, capped at the capital; whole shares only."""
    if stop_pct >= 0 or entry_price <= 0:
        raise InvalidPlanError("stop-loss % must be negative and the entry price positive")
    risk_amount = capital * risk_pct / 100
    budget = min(capital, risk_amount / (abs(stop_pct) / 100))
    quantity = int((budget / entry_price).to_integral_value(rounding=ROUND_DOWN))
    return PositionSize(
        amount=(entry_price * quantity).quantize(PAISE, rounding=ROUND_HALF_UP),
        quantity=quantity,
        risk_amount=risk_amount.quantize(PAISE, rounding=ROUND_HALF_UP),
    )
