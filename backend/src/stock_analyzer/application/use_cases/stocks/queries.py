"""Read-only stock queries for the API."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import Prediction
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.shared.percent import return_pct
from stock_analyzer.domain.stock.stock import Stock


@dataclass(frozen=True, slots=True)
class StockPredictions:
    """A stock with its latest prediction per holding category and its last close."""

    stock: Stock
    last_close: Candle | None
    predictions: list[Prediction]


@dataclass(frozen=True, slots=True)
class StockOverview:
    """One row of the Stocks table: last price, recent moves and the 1Y prediction."""

    stock: Stock
    last_close: Candle | None
    day_change_pct: Decimal | None
    return_1y_pct: Decimal | None
    median_1y_pct: Decimal | None
    prob_up_1y: Decimal | None


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

    async def overview(self, limit: int = 100) -> list[StockOverview]:
        """Return every stock with its last close, day change, 1Y return and 1Y prediction."""
        async with self._uow_factory() as uow:
            stocks = await uow.stocks.search(None, limit)
            rows = []
            for stock in stocks:
                stock_id = stock.id or 0
                latest = await uow.prices.get_candles(stock_id)
                last = latest[-1] if latest else None
                prev = latest[-2] if len(latest) > 1 else None
                year_ago = (
                    next(
                        (
                            c
                            for c in latest
                            if c.trade_date >= last.trade_date - timedelta(days=365)
                        ),
                        None,
                    )
                    if last
                    else None
                )
                one_year = next(
                    (
                        p
                        for p in await uow.predictions.latest_for_stock(stock_id)
                        if p.category is HoldingCategory.Y1
                    ),
                    None,
                )
                rows.append(
                    StockOverview(
                        stock=stock,
                        last_close=last,
                        day_change_pct=return_pct(prev.close, last.close)
                        if last and prev
                        else None,
                        return_1y_pct=(
                            return_pct(year_ago.adj_close, last.adj_close)
                            if last and year_ago
                            else None
                        ),
                        median_1y_pct=one_year.range.p50_pct if one_year else None,
                        prob_up_1y=one_year.prob_up if one_year else None,
                    )
                )
        return rows

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

    async def fundamentals(self, symbol: str) -> list[QuarterlyFundamentals]:
        """Return the stock's quarterly results, oldest first."""
        stock = await self.get(symbol)
        async with self._uow_factory() as uow:
            return await uow.fundamentals.list_quarters(stock.id or 0)

    async def predictions(self, symbol: str) -> StockPredictions:
        """Return the latest prediction per category and the last close."""
        stock = await self.get(symbol)
        async with self._uow_factory() as uow:
            predictions = await uow.predictions.latest_for_stock(stock.id or 0)
            candles = await uow.prices.get_candles(stock.id or 0)
        return StockPredictions(
            stock=stock, last_close=candles[-1] if candles else None, predictions=predictions
        )
