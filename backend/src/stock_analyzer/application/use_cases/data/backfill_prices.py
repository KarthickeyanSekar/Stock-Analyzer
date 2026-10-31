"""Load instruments and daily candles from a market data provider into the database."""

from dataclasses import dataclass
from datetime import date

from stock_analyzer.application.ports.market_data import MarketDataProvider
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory

MARKETS = {"IN": ("India", "INR", "Asia/Kolkata")}


@dataclass(frozen=True, slots=True)
class BackfillResult:
    """How much was loaded."""

    stocks: int
    candles: int


class BackfillPrices:
    """Idempotent backfill: re-running replaces existing rows instead of duplicating them."""

    def __init__(self, uow_factory: UnitOfWorkFactory, provider: MarketDataProvider) -> None:
        """Load data from ``provider`` using fresh units of work."""
        self._uow_factory = uow_factory
        self._provider = provider

    async def execute(self, start: date, end: date) -> BackfillResult:
        """Upsert every instrument and its candles from ``start`` to ``end``."""
        instruments = self._provider.list_instruments()
        async with self._uow_factory() as uow:
            for code in {stock.market_code for stock in instruments}:
                name, currency, timezone = MARKETS[code]
                await uow.stocks.ensure_market(code, name, currency, timezone)
            await uow.providers.ensure(self._provider.name, "MARKET_DATA", "Mock (synthetic data)")
            stocks = await uow.stocks.upsert_many(instruments)
            await uow.commit()

        total = 0
        for stock in stocks:
            if stock.id is None:  # pragma: no cover - upsert always returns ids
                continue
            candles = self._provider.daily_candles(stock.symbol, start, end)
            async with self._uow_factory() as uow:
                total += await uow.prices.upsert_candles(stock.id, candles, self._provider.name)
                await uow.commit()
        return BackfillResult(stocks=len(stocks), candles=total)
