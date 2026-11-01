"""Quarterly fundamentals value object (point-in-time: usable only from ``announced_date``)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QuarterlyFundamentals:
    """Key figures for one reporting quarter; money in the stock's currency, crore units."""

    period_end: date
    announced_date: date
    revenue_cr: Decimal
    net_profit_cr: Decimal
    eps: Decimal
    book_value_per_share: Decimal
    roe_pct: Decimal
    debt_to_equity: Decimal

    def __post_init__(self) -> None:
        """Reject figures that can't be true."""
        if self.announced_date <= self.period_end:
            raise ValueError(f"results for {self.period_end} announced before the quarter ended")
        if self.revenue_cr < 0 or self.book_value_per_share <= 0 or self.debt_to_equity < 0:
            raise ValueError(f"impossible fundamentals for {self.period_end}")

    def is_known_on(self, day: date) -> bool:
        """Whether these numbers were public on ``day`` (no look-ahead)."""
        return self.announced_date <= day
