"""SQLAlchemy provider configuration repository."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.infrastructure.persistence.models import ProviderModel


class SqlAlchemyProviderRepository:
    """Configured provider plugins."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def ensure(self, plugin_name: str, kind: str, display_name: str) -> None:
        """Register the provider if it isn't configured yet."""
        statement = insert(ProviderModel).values(
            plugin_name=plugin_name, kind=kind, display_name=display_name
        )
        await self._session.execute(
            statement.on_conflict_do_nothing(index_elements=["plugin_name"])
        )

    async def list_all(self) -> list[tuple[str, str, str, bool]]:
        """Return ``(plugin_name, kind, display_name, is_enabled)`` for every provider."""
        rows = await self._session.scalars(select(ProviderModel).order_by(ProviderModel.id))
        return [(r.plugin_name, r.kind, r.display_name, r.is_enabled) for r in rows]
