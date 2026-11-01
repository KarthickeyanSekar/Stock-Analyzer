"""SQLAlchemy fundamentals repository."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.infrastructure.persistence.models import FundamentalsModel

QUARTER = "Q"
# Decimals are stored as JSON strings so no precision is lost through floats.
STATEMENT_FIELDS = ("revenue_cr", "net_profit_cr", "eps", "book_value_per_share")
RATIO_FIELDS = ("roe_pct", "debt_to_equity")


class SqlAlchemyFundamentalsRepository:
    """Quarterly results in the ``fundamentals`` table (statements + ratios as JSONB)."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def upsert_quarters(
        self, stock_id: int, quarters: Sequence[QuarterlyFundamentals], source_provider: str
    ) -> int:
        """Insert or replace quarters by period end; return how many were written."""
        if not quarters:
            return 0
        rows = [
            {
                "stock_id": stock_id,
                "period_end": q.period_end,
                "period_type": QUARTER,
                "announced_date": q.announced_date,
                "statements": {field: str(getattr(q, field)) for field in STATEMENT_FIELDS},
                "ratios": {field: str(getattr(q, field)) for field in RATIO_FIELDS},
                "source_provider": source_provider,
            }
            for q in quarters
        ]
        statement = insert(FundamentalsModel).values(rows)
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=["stock_id", "period_end", "period_type"],
                set_={
                    column: statement.excluded[column]
                    for column in ("announced_date", "statements", "ratios", "source_provider")
                },
            )
        )
        return len(quarters)

    async def list_quarters(
        self, stock_id: int, known_on: date | None = None
    ) -> list[QuarterlyFundamentals]:
        """Return quarters in period order; with ``known_on``, only those announced by then."""
        statement = select(FundamentalsModel).where(
            FundamentalsModel.stock_id == stock_id, FundamentalsModel.period_type == QUARTER
        )
        if known_on:
            statement = statement.where(FundamentalsModel.announced_date <= known_on)
        rows = await self._session.scalars(statement.order_by(FundamentalsModel.period_end))
        return [
            QuarterlyFundamentals(
                period_end=r.period_end,
                announced_date=r.announced_date or r.period_end,
                **{field: Decimal(r.statements[field]) for field in STATEMENT_FIELDS},
                **{field: Decimal(r.ratios[field]) for field in RATIO_FIELDS},
            )
            for r in rows
        ]

    async def delete_by_source(self, source_provider: str) -> int:
        """Delete every quarter from one provider; return how many."""
        result = await self._session.execute(
            delete(FundamentalsModel).where(FundamentalsModel.source_provider == source_provider)
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]
