"""SQLAlchemy stock repository."""

from collections.abc import Sequence

from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.application.ports.repositories import StockDataSource
from stock_analyzer.domain.stock.stock import Stock
from stock_analyzer.infrastructure.persistence.models import (
    MarketModel,
    PriceDailyModel,
    StockModel,
)


def _to_domain(row: StockModel) -> Stock:
    return Stock(
        id=row.id,
        market_code=row.market_code,
        exchange=row.exchange,
        symbol=row.symbol,
        name=row.name,
        sector=row.sector,
        currency=row.currency,
        timezone=row.timezone,
        source_provider=row.source_provider,
    )


class SqlAlchemyStockRepository:
    """Stocks and markets stored in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def ensure_market(self, code: str, name: str, currency: str, timezone: str) -> None:
        """Create the market if it doesn't exist."""
        statement = insert(MarketModel).values(
            code=code, name=name, currency=currency, timezone=timezone
        )
        await self._session.execute(statement.on_conflict_do_nothing(index_elements=["code"]))

    async def upsert_many(self, stocks: Sequence[Stock]) -> list[Stock]:
        """Insert or update stocks by (exchange, symbol) and return them with ids."""
        if not stocks:
            return []
        rows = [
            {
                "market_code": s.market_code,
                "exchange": s.exchange,
                "symbol": s.symbol,
                "name": s.name,
                "sector": s.sector,
                "currency": s.currency,
                "timezone": s.timezone,
                "source_provider": s.source_provider,
            }
            for s in stocks
        ]
        statement = insert(StockModel).values(rows)
        upsert = statement.on_conflict_do_update(
            index_elements=["exchange", "symbol"],
            set_={
                "name": statement.excluded.name,
                "sector": statement.excluded.sector,
                "source_provider": statement.excluded.source_provider,
            },
        ).returning(StockModel)
        result = await self._session.scalars(upsert)
        return [_to_domain(row) for row in result]

    async def search(self, query: str | None, limit: int) -> list[Stock]:
        """Return active stocks whose symbol or name contains ``query``."""
        statement = select(StockModel).where(StockModel.is_active.is_(True))
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(StockModel.symbol.ilike(pattern), StockModel.name.ilike(pattern))
            )
        result = await self._session.scalars(statement.order_by(StockModel.symbol).limit(limit))
        return [_to_domain(row) for row in result]

    async def get_by_symbol(self, symbol: str, exchange: str = "NSE") -> Stock | None:
        """Return one stock, or ``None``."""
        row = await self._session.scalar(
            select(StockModel).where(StockModel.exchange == exchange, StockModel.symbol == symbol)
        )
        return _to_domain(row) if row else None

    async def get(self, stock_id: int) -> Stock | None:
        """Return one stock by id, or ``None``."""
        row = await self._session.get(StockModel, stock_id)
        return _to_domain(row) if row else None

    async def data_sources(self) -> list[StockDataSource]:
        """Every active stock with its price source and sync flag, by symbol."""
        latest = (
            select(
                PriceDailyModel.stock_id,
                func.max(PriceDailyModel.trade_date).label("last_date"),
                func.count().label("candles"),
            )
            .group_by(PriceDailyModel.stock_id)
            .subquery()
        )
        source = (
            select(PriceDailyModel.source_provider)
            .where(
                PriceDailyModel.stock_id == latest.c.stock_id,
                PriceDailyModel.trade_date == latest.c.last_date,
            )
            .scalar_subquery()
        )
        statement = (
            select(StockModel, latest.c.last_date, latest.c.candles, source)
            .outerjoin(latest, latest.c.stock_id == StockModel.id)
            .where(StockModel.is_active.is_(True))
            .order_by(StockModel.symbol)
        )
        rows = await self._session.execute(statement)
        return [
            StockDataSource(
                stock=_to_domain(row),
                is_real_sync_enabled=row.is_real_sync_enabled,
                latest_source=latest_source,
                last_trade_date=last_date,
                candles=int(candles or 0),
            )
            for row, last_date, candles, latest_source in rows
        ]

    async def set_real_sync(self, stock_id: int, *, is_enabled: bool) -> None:
        """Pick or unpick the stock for the real-data sync."""
        await self._session.execute(
            update(StockModel)
            .where(StockModel.id == stock_id)
            .values(is_real_sync_enabled=is_enabled)
        )

    async def real_sync_stocks(self) -> list[Stock]:
        """Stocks picked for the real-data sync, by symbol."""
        result = await self._session.scalars(
            select(StockModel)
            .where(StockModel.is_real_sync_enabled.is_(True), StockModel.is_active.is_(True))
            .order_by(StockModel.symbol)
        )
        return [_to_domain(row) for row in result]

    async def set_source_provider(self, stock_id: int, source_provider: str) -> None:
        """Record which provider the stock's data now comes from."""
        await self._session.execute(
            update(StockModel)
            .where(StockModel.id == stock_id)
            .values(source_provider=source_provider)
        )
