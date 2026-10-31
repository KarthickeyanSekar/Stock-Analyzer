"""Deterministic synthetic price generator (regime-switching geometric Brownian motion).

A shared market factor switches between bull, sideways and bear regimes; each stock adds
its sector's drift and volatility. Same seed → identical data, so tests and demos repeat.
"""

import math
import random
import zlib
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.pricing.candle import Candle

TRADING_DAYS_PER_YEAR = 250
TICK = Decimal("0.05")  # NSE price step
# (annual drift, annual volatility) of the market factor per regime.
REGIMES: dict[str, tuple[float, float]] = {
    "bull": (0.22, 0.13),
    "sideways": (0.03, 0.15),
    "bear": (-0.25, 0.28),
}
# Daily probability of switching to each other regime.
REGIME_SWITCH_PROB = 0.008


@dataclass(frozen=True, slots=True)
class StockProfile:
    """Statistical profile of one synthetic stock."""

    symbol: str
    drift: float
    volatility: float
    beta: float
    start_price: float


def _to_price(value: float) -> Decimal:
    """Round a float price to the NSE tick size."""
    ticks = (Decimal(str(value)) / TICK).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return max(ticks, Decimal(1)) * TICK


class SyntheticMarket:
    """Generates daily candles for many stocks from one shared, seeded market factor."""

    def __init__(self, calendar: TradingCalendar, start: date, end: date, seed: int) -> None:
        """Prepare the trading days and the market factor for ``start`` to ``end``."""
        self._seed = seed
        self.trading_days = calendar.trading_days(start, end)
        self.market_returns = self._market_factor()

    def _market_factor(self) -> list[float]:
        rng = random.Random(self._seed)  # noqa: S311 - synthetic data, not security
        regime, returns = "bull", []
        dt = 1 / TRADING_DAYS_PER_YEAR
        for _ in self.trading_days:
            if rng.random() < REGIME_SWITCH_PROB * (len(REGIMES) - 1):
                regime = rng.choice([name for name in REGIMES if name != regime])
            drift, volatility = REGIMES[regime]
            returns.append(
                (drift - volatility**2 / 2) * dt + volatility * math.sqrt(dt) * rng.gauss()
            )
        return returns

    def candles(self, profile: StockProfile, split: tuple[date, int] | None = None) -> list[Candle]:
        """Return the stock's candles; before a split, raw prices are ``ratio`` times higher."""
        rng = random.Random(self._seed ^ zlib.crc32(profile.symbol.encode()))  # noqa: S311
        dt = 1 / TRADING_DAYS_PER_YEAR
        idio_vol = math.sqrt(max(profile.volatility**2 - (profile.beta * 0.15) ** 2, 0.01))
        price, candles = profile.start_price, []
        for day, market in zip(self.trading_days, self.market_returns, strict=True):
            idio = (profile.drift - idio_vol**2 / 2) * dt + idio_vol * math.sqrt(dt) * rng.gauss()
            open_price = price * math.exp(rng.gauss() * 0.004)  # overnight gap
            close_price = price * math.exp(profile.beta * market + idio)
            high = max(open_price, close_price) * (1 + abs(rng.gauss()) * 0.006)
            low = min(open_price, close_price) * (1 - abs(rng.gauss()) * 0.006)
            factor = split[1] if split and day < split[0] else 1
            raw = [_to_price(value * factor) for value in (open_price, high, low, close_price)]
            raw[1] = max(raw)  # keep OHLC consistent after rounding
            raw[2] = min(raw)
            candles.append(
                Candle(
                    trade_date=day,
                    open=raw[0],
                    high=raw[1],
                    low=raw[2],
                    close=raw[3],
                    adj_close=_to_price(close_price),
                    volume=int(rng.lognormvariate(14, 0.5)),
                )
            )
            price = close_price
        return candles
