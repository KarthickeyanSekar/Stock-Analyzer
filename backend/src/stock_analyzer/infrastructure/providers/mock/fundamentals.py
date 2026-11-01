"""Deterministic synthetic quarterly results that grow with each stock's drift."""

import random
import zlib
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.infrastructure.providers.mock.generator import StockProfile

CENTS = Decimal("0.01")
# Share of quarterly profit kept as equity (the rest is paid out as dividends).
RETENTION = 0.7
QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def quarter_ends(start: date, end: date) -> list[date]:
    """Return every calendar quarter end between ``start`` and ``end`` (inclusive)."""
    return [
        day
        for year in range(start.year, end.year + 1)
        for month, last in QUARTER_ENDS
        if start <= (day := date(year, month, last)) <= end
    ]


def synthetic_quarters(
    profile: StockProfile, start: date, end: date, seed: int
) -> list[QuarterlyFundamentals]:
    """Generate quarters ending ``start``..``end`` that were announced by ``end``."""
    rng = random.Random(seed ^ zlib.crc32(profile.symbol.encode()) ^ 0x5F5F)  # noqa: S311
    shares_cr = rng.uniform(50, 1500)
    revenue = rng.uniform(5_000, 200_000) / 4
    margin = rng.uniform(0.06, 0.22)
    equity = revenue * 4 * margin * rng.uniform(4, 8)
    debt_to_equity = rng.uniform(0.05, 1.5)
    quarterly_growth = (1 + profile.drift) ** 0.25

    quarters = []
    for period_end in quarter_ends(start, end):
        revenue *= quarterly_growth * rng.uniform(0.97, 1.03)
        profit = revenue * margin * rng.uniform(0.85, 1.15)
        roe = profit * 4 / equity * 100
        equity += profit * RETENTION
        debt_to_equity = max(0.0, debt_to_equity + rng.uniform(-0.05, 0.05))
        announced = period_end + timedelta(days=30 + rng.randint(0, 15))
        if announced > end:
            break
        quarters.append(
            QuarterlyFundamentals(
                period_end=period_end,
                announced_date=announced,
                revenue_cr=_money(revenue),
                net_profit_cr=_money(profit),
                eps=_money(profit / shares_cr),
                book_value_per_share=_money(equity / shares_cr),
                roe_pct=_money(roe),
                debt_to_equity=_money(debt_to_equity),
            )
        )
    return quarters
