"""SQLAlchemy stock repository."""

from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.stock.stock import Stock
from stock_analyzer.infrastructure.persistence.models import MarketModel, StockModel


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
