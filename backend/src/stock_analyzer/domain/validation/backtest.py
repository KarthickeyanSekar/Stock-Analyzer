"""Simulate full trade plans and summarise them (docs/12-entry-exit-strategy.md §5-6; Q69).

Floats inside (Q64). Conservative tax: gains taxed per trade, no annual LTCG exemption and no
loss set-off, so real results can only be better.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

TRADING_DAYS_PER_YEAR = 250
DEFAULT_ROUND_TRIP_COST_PCT = 0.25
STCG_PCT = 20.0  # held under a year (Budget 2024)
LTCG_PCT = 12.5  # held a year or more (Budget 2024)


class ExitReason(StrEnum):
    """Which barrier ended the plan."""

    TARGET = "TARGET"
    STOP = "STOP"
    TIME = "TIME"


@dataclass(frozen=True, slots=True)
class CostModel:
    """Trading costs and capital-gains tax (Q69); all values in percent."""

    round_trip_cost_pct: float = DEFAULT_ROUND_TRIP_COST_PCT
    stcg_pct: float = STCG_PCT
    ltcg_pct: float = LTCG_PCT

    def net(self, gross_pct: float, calendar_days: int) -> float:
        """Return after costs and, for gains, the capital-gains tax."""
        after_costs = gross_pct - self.round_trip_cost_pct
        if after_costs <= 0:
            return after_costs  # no tax on a loss (and no set-off: conservative)
        rate = self.ltcg_pct if calendar_days >= 365 else self.stcg_pct  # noqa: PLR2004
        return after_costs * (1 - rate / 100)


@dataclass(frozen=True, slots=True)
class Trade:
    """One simulated plan."""

    symbol: str
    category: str
    start_date: date
    gross_pct: float
    net_pct: float
    days: int  # trading days held
    exit_reason: ExitReason
    benchmark_pct: float  # benchmark return over the same days, after the same costs/tax
    predicted_prob: float  # predicted chance of the target when the plan started


def simulate(
    future_closes: Sequence[float],
    entry: float,
    target_pct: float,
    stop_pct: float,
    horizon: int,
) -> tuple[float, int, ExitReason] | None:
    """Gross return %, trading days held and exit reason; ``None`` if the data ends too early.

    Exits on the first close at/above the target or at/below the stop, else at the horizon.
    """
    if entry <= 0 or len(future_closes) < horizon or horizon <= 0:
        return None
    for day, price in enumerate(future_closes[:horizon], start=1):
        change = (price / entry - 1) * 100
        if change >= target_pct:
            return change, day, ExitReason.TARGET
        if change <= stop_pct:
            return change, day, ExitReason.STOP
    return (future_closes[horizon - 1] / entry - 1) * 100, horizon, ExitReason.TIME


@dataclass(frozen=True, slots=True)
class TradeSummary:
    """Metrics of a set of trades (doc 12 §6)."""

    trades: int
    win_rate: float
    avg_gain_pct: float | None
    avg_loss_pct: float | None
    expectancy_pct: float  # mean net return per trade
    benchmark_expectancy_pct: float
    avg_days: float
    target_hit_rate: float
    avg_predicted_prob: float
    beats_benchmark: bool


def summarise(trades: Sequence[Trade]) -> TradeSummary | None:
    """Summary metrics, or ``None`` without trades."""
    if not trades:
        return None
    n = len(trades)
    gains = [t.net_pct for t in trades if t.net_pct > 0]
    losses = [t.net_pct for t in trades if t.net_pct <= 0]
    expectancy = sum(t.net_pct for t in trades) / n
    benchmark = sum(t.benchmark_pct for t in trades) / n
    return TradeSummary(
        trades=n,
        win_rate=len(gains) / n,
        avg_gain_pct=sum(gains) / len(gains) if gains else None,
        avg_loss_pct=sum(losses) / len(losses) if losses else None,
        expectancy_pct=expectancy,
        benchmark_expectancy_pct=benchmark,
        avg_days=sum(t.days for t in trades) / n,
        target_hit_rate=sum(t.exit_reason is ExitReason.TARGET for t in trades) / n,
        avg_predicted_prob=sum(t.predicted_prob for t in trades) / n,
        beats_benchmark=expectancy > benchmark,
    )
