"""Stock entity: a listed instrument on one exchange of a market."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Stock:
    """A stock as the rest of the system sees it (market-agnostic)."""

    market_code: str
    exchange: str
    symbol: str
    name: str
    sector: str | None
    currency: str
    timezone: str
    source_provider: str
    id: int | None = None
