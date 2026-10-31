"""SQLAlchemy daily price repository."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.infrastructure.persistence.models import PriceDailyModel

BATCH_SIZE = 1000


class SqlAlchemyPriceRepository:
    """Daily candles in the ``prices_daily`` hypertable."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def upsert_candles(
        self, stock_id: int, candles: Sequence[Candle], source_provider: str
    ) -> int:
        """Insert or replace candles in batches; return how many were written."""
        for offset in range(0, len(candles), BATCH_SIZE):
            rows = [
                {
                    "stock_id": stock_id,
                    "trade_date": c.trade_date,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "adj_close": c.adj_close,
                    "volume": c.volume,
                    "source_provider": source_provider,
                }
                for c in candles[offset : offset + BATCH_SIZE]
            ]
            statement = insert(PriceDailyModel).values(rows)
            await self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=["stock_id", "trade_date"],
                    set_={
                        column: statement.excluded[column]
                        for column in ("open", "high", "low", "close", "adj_close", "volume")
                    }
                    | {"source_provider": statement.excluded.source_provider},
                )
            )
        return len(candles)

    async def get_candles(
        self, stock_id: int, start: date | None = None, end: date | None = None
    ) -> list[Candle]:
        """Return candles in date order."""
        statement = select(PriceDailyModel).where(PriceDailyModel.stock_id == stock_id)
        if start:
            statement = statement.where(PriceDailyModel.trade_date >= start)
        if end:
            statement = statement.where(PriceDailyModel.trade_date <= end)
        rows = await self._session.scalars(statement.order_by(PriceDailyModel.trade_date))
        return [
            Candle(
                trade_date=r.trade_date,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                adj_close=r.adj_close,
                volume=r.volume,
            )
            for r in rows
        ]
