"""Read-only stock queries for the API."""

from dataclasses import dataclass
from datetime import date

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.prediction.prediction import Prediction
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock


@dataclass(frozen=True, slots=True)
class StockPredictions:
    """A stock with its latest prediction per holding category and its last close."""

    stock: Stock
    last_close: Candle | None
    predictions: list[Prediction]


class StockQueries:
    """Search stocks, read prices and predictions."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work per query."""
        self._uow_factory = uow_factory

    async def search(self, query: str | None, limit: int = 20) -> list[Stock]:
        """Return stocks matching ``query`` by symbol or name."""
        async with self._uow_factory() as uow:
            return await uow.stocks.search(query, limit)

    async def get(self, symbol: str) -> Stock:
        """Return one stock or raise :class:`NotFoundError`."""
        async with self._uow_factory() as uow:
            stock = await uow.stocks.get_by_symbol(symbol)
        if stock is None:
            raise NotFoundError(f"stock {symbol} not found")
        return stock

    async def symbols(self, stock_ids: set[int]) -> dict[int, str]:
        """Return ``{stock_id: symbol}`` for the given ids (unknown ids are skipped)."""
        found: dict[int, str] = {}
        async with self._uow_factory() as uow:
            for stock_id in stock_ids:
                stock = await uow.stocks.get(stock_id)
                if stock is not None:
                    found[stock_id] = stock.symbol
        return found

    async def prices(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> list[Candle]:
        """Return the stock's candles between ``start`` and ``end``."""
        stock = await self.get(symbol)
        async with self._uow_factory() as uow:
            return await uow.prices.get_candles(stock.id or 0, start, end)

    async def predictions(self, symbol: str) -> StockPredictions:
        """Return the latest prediction per category and the last close."""
        stock = await self.get(symbol)
        async with self._uow_factory() as uow:
            predictions = await uow.predictions.latest_for_stock(stock.id or 0)
            candles = await uow.prices.get_candles(stock.id or 0)
        return StockPredictions(
            stock=stock, last_close=candles[-1] if candles else None, predictions=predictions
        )
