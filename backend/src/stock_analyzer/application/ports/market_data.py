"""Market data provider port: implemented by the mock plugin now, real APIs later."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock


@dataclass(frozen=True, slots=True)
class ConnectionCheck:
    """Result of a provider connection test; ``message`` never contains secrets."""

    is_ok: bool
    message: str


class MarketDataProvider(Protocol):
    """Source of instruments and end-of-day candles for one market."""

    @property
    def name(self) -> str:
        """Plugin name stored as ``source_provider`` on every record (e.g., ``mock``)."""
        ...

    def list_instruments(self) -> Sequence[Stock]:
        """Return the instruments this provider covers (without database ids)."""
        ...

    def daily_candles(self, symbol: str, start: date, end: date) -> Sequence[Candle]:
        """Return adjusted daily candles for ``symbol`` between ``start`` and ``end``."""
        ...

    def test_connection(self) -> ConnectionCheck:
        """Check that the provider is reachable with its configured credentials."""
        ...
