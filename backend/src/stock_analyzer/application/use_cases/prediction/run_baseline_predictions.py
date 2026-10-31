"""Compute and store the empirical baseline prediction for every stock and category."""

from datetime import date

from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.baseline import empirical_prediction

ALGORITHM = "empirical-forward-returns"
MAX_STOCKS = 10_000


class RunBaselinePredictions:
    """Batch job: one prediction per stock x holding category, as of the latest close."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work for reading and writing."""
        self._uow_factory = uow_factory

    async def execute(self, as_of: date | None = None) -> int:
        """Return how many predictions were stored (``as_of`` defaults to each stock's last day)."""
        async with self._uow_factory() as uow:
            stocks = await uow.stocks.search(None, MAX_STOCKS)
        stored = 0
        for stock in stocks:
            if stock.id is None:  # pragma: no cover
                continue
            async with self._uow_factory() as uow:
                candles = await uow.prices.get_candles(stock.id, end=as_of)
                if not candles:
                    continue
                prediction_date = as_of or candles[-1].trade_date
                closes = [(c.trade_date, c.adj_close) for c in candles]
                predictions = [
                    prediction
                    for category in HoldingCategory
                    if (
                        prediction := empirical_prediction(
                            stock_id=stock.id,
                            as_of=prediction_date,
                            category=category,
                            closes=closes,
                        )
                    )
                ]
                stored += await uow.predictions.save_many(predictions, ALGORITHM)
                await uow.commit()
        return stored
