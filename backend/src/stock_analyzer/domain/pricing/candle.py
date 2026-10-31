"""Daily OHLCV candle value object."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    """One end-of-day candle; ``adj_close`` is adjusted for splits and bonuses."""

    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal
    volume: int

    def __post_init__(self) -> None:
        """Reject candles whose prices are inconsistent."""
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError(f"inconsistent OHLC on {self.trade_date}")
        if self.low <= 0 or self.volume < 0:
            raise ValueError(f"non-positive price or negative volume on {self.trade_date}")
