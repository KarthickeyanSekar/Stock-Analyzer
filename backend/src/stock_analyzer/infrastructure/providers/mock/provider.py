"""Mock market data + fundamentals provider: synthetic NIFTY 50 data behind the real ports."""

import random
import zlib
from collections.abc import Sequence
from datetime import date

from stock_analyzer.application.ports.market_data import ConnectionCheck
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock
from stock_analyzer.infrastructure.providers.mock.fundamentals import synthetic_quarters
from stock_analyzer.infrastructure.providers.mock.generator import StockProfile, SyntheticMarket
from stock_analyzer.infrastructure.providers.mock.universe import (
    NIFTY50,
    SAMPLE_HOLIDAYS,
    SAMPLE_SPLITS,
    SECTOR_PROFILE,
)

PLUGIN_NAME = "mock"
DEFAULT_SEED = 42
DEFAULT_START = date(2021, 11, 1)
DEFAULT_END = date(2026, 10, 30)


class MockMarketDataProvider:
    """Deterministic synthetic data for 50 NSE stocks; every record is labelled ``mock``."""

    def __init__(
        self, seed: int = DEFAULT_SEED, start: date = DEFAULT_START, end: date = DEFAULT_END
    ) -> None:
        """Generate the market factor once; per-stock candles are generated on demand."""
        self._seed = seed
        self._start, self._end = start, end
        self._market = SyntheticMarket(TradingCalendar(SAMPLE_HOLIDAYS), start, end, seed)
        self._splits = {symbol: (ex_date, ratio) for symbol, ex_date, ratio in SAMPLE_SPLITS}
        self._cache: dict[str, list[Candle]] = {}
        self._quarters: dict[str, list[QuarterlyFundamentals]] = {}

    @property
    def name(self) -> str:
        """Plugin name stored as ``source_provider``."""
        return PLUGIN_NAME

    def list_instruments(self) -> Sequence[Stock]:
        """Return the 50 synthetic NSE stocks."""
        return [
            Stock(
                market_code="IN",
                exchange="NSE",
                symbol=symbol,
                name=name,
                sector=sector,
                currency="INR",
                timezone="Asia/Kolkata",
                source_provider=PLUGIN_NAME,
            )
            for symbol, name, sector in NIFTY50
        ]

    def daily_candles(self, symbol: str, start: date, end: date) -> Sequence[Candle]:
        """Return the synthetic candles for ``symbol`` between ``start`` and ``end``."""
        if symbol not in self._cache:
            self._cache[symbol] = self._market.candles(
                self._profile(symbol), self._splits.get(symbol)
            )
        return [candle for candle in self._cache[symbol] if start <= candle.trade_date <= end]

    def quarterly_fundamentals(
        self, symbol: str, start: date, end: date
    ) -> Sequence[QuarterlyFundamentals]:
        """Return synthetic quarters ending ``start``..``end`` that were announced by ``end``."""
        if symbol not in self._quarters:
            self._quarters[symbol] = synthetic_quarters(
                self._profile(symbol), self._start, self._end, self._seed
            )
        return [
            q
            for q in self._quarters[symbol]
            if start <= q.period_end <= end and q.announced_date <= end
        ]

    def test_connection(self) -> ConnectionCheck:
        """The mock provider is always available."""
        return ConnectionCheck(is_ok=True, message="Synthetic data, always available")

    def _profile(self, symbol: str) -> StockProfile:
        sector = next(sector for sym, _, sector in NIFTY50 if sym == symbol)
        drift, volatility, beta = SECTOR_PROFILE[sector]
        rng = random.Random(self._seed ^ zlib.crc32(symbol.encode()) ^ 0xA5A5)  # noqa: S311
        return StockProfile(
            symbol=symbol,
            drift=drift + rng.uniform(-0.04, 0.04),
            volatility=volatility * rng.uniform(0.85, 1.15),
            beta=beta,
            start_price=round(rng.uniform(150, 4500), 2),
        )
