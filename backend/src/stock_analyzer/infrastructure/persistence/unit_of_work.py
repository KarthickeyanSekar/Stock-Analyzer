"""SQLAlchemy unit of work: one session (transaction) shared by every repository."""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from stock_analyzer.infrastructure.persistence.repositories.fundamentals import (
    SqlAlchemyFundamentalsRepository,
)
from stock_analyzer.infrastructure.persistence.repositories.predictions import (
    SqlAlchemyPredictionRepository,
)
from stock_analyzer.infrastructure.persistence.repositories.prices import SqlAlchemyPriceRepository
from stock_analyzer.infrastructure.persistence.repositories.providers import (
    SqlAlchemyProviderRepository,
)
from stock_analyzer.infrastructure.persistence.repositories.stocks import SqlAlchemyStockRepository
from stock_analyzer.infrastructure.persistence.repositories.trade_plans import (
    SqlAlchemyTradePlanRepository,
)


class _Repositories:
    """Repositories bound to one open session."""

    def __init__(self, session: AsyncSession) -> None:
        self.stocks = SqlAlchemyStockRepository(session)
        self.prices = SqlAlchemyPriceRepository(session)
        self.fundamentals = SqlAlchemyFundamentalsRepository(session)
        self.predictions = SqlAlchemyPredictionRepository(session)
        self.trade_plans = SqlAlchemyTradePlanRepository(session)
        self.providers = SqlAlchemyProviderRepository(session)


class SqlAlchemyUnitOfWork:
    """Opens a session on enter; rolls back anything not committed on exit."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Create the unit of work; the session opens on ``async with``."""
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._repos: _Repositories | None = None

    def _bound(self) -> _Repositories:
        if self._repos is None:
            raise RuntimeError("unit of work used outside 'async with'")
        return self._repos

    @property
    def stocks(self) -> SqlAlchemyStockRepository:
        """Stock repository bound to this transaction."""
        return self._bound().stocks

    @property
    def prices(self) -> SqlAlchemyPriceRepository:
        """Price repository bound to this transaction."""
        return self._bound().prices

    @property
    def fundamentals(self) -> SqlAlchemyFundamentalsRepository:
        """Fundamentals repository bound to this transaction."""
        return self._bound().fundamentals

    @property
    def predictions(self) -> SqlAlchemyPredictionRepository:
        """Prediction repository bound to this transaction."""
        return self._bound().predictions

    @property
    def trade_plans(self) -> SqlAlchemyTradePlanRepository:
        """Trade plan repository bound to this transaction."""
        return self._bound().trade_plans

    @property
    def providers(self) -> SqlAlchemyProviderRepository:
        """Provider repository bound to this transaction."""
        return self._bound().providers

    async def __aenter__(self) -> Self:
        """Open the session and bind the repositories to it."""
        self._session = self._session_factory()
        self._repos = _Repositories(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Roll back uncommitted work and close the session."""
        if self._session is not None:
            await self._session.rollback()
            await self._session.close()
        self._session, self._repos = None, None

    async def commit(self) -> None:
        """Commit the transaction."""
        if self._session is None:
            raise RuntimeError("unit of work used outside 'async with'")
        await self._session.commit()
