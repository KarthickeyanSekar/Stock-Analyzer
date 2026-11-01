"""Load quarterly fundamentals from a fundamentals provider into the database."""

from datetime import date

from stock_analyzer.application.ports.fundamentals import FundamentalsProvider
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory


class BackfillFundamentals:
    """Idempotent backfill for every stock already in the database (run after prices)."""

    def __init__(self, uow_factory: UnitOfWorkFactory, provider: FundamentalsProvider) -> None:
        """Load data from ``provider`` using fresh units of work."""
        self._uow_factory = uow_factory
        self._provider = provider

    async def execute(self, start: date, end: date, limit: int = 1000) -> int:
        """Upsert quarters ending ``start``..``end`` for every stock; return how many."""
        async with self._uow_factory() as uow:
            stocks = await uow.stocks.search(None, limit)

        total = 0
        for stock in stocks:
            if stock.id is None:  # pragma: no cover - stored stocks always have ids
                continue
            quarters = self._provider.quarterly_fundamentals(stock.symbol, start, end)
            async with self._uow_factory() as uow:
                total += await uow.fundamentals.upsert_quarters(
                    stock.id, quarters, self._provider.name
                )
                await uow.commit()
        return total
