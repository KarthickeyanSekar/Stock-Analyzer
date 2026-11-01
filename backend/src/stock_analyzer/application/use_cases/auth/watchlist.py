"""A user's watchlist."""

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.stock.stock import Stock
from stock_analyzer.domain.users.user import User


class WatchlistService:
    """List, add and remove watched stocks for the signed-in user."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        """Use fresh units of work per call."""
        self._uow_factory = uow_factory

    async def list(self, user: User) -> list[Stock]:
        """Watched stocks in the order they were added."""
        async with self._uow_factory() as uow:
            ids = await uow.watchlists.list_for(user.id)
            return [s for i in ids if (s := await uow.stocks.get(i)) is not None]

    async def set(self, user: User, symbol: str, *, watched: bool) -> None:
        """Watch or stop watching ``symbol``."""
        async with self._uow_factory() as uow:
            stock = await uow.stocks.get_by_symbol(symbol)
            if stock is None or stock.id is None:
                raise NotFoundError(f"stock {symbol} not found")
            if watched:
                await uow.watchlists.add(user.id, stock.id)
            else:
                await uow.watchlists.remove(user.id, stock.id)
            await uow.commit()
