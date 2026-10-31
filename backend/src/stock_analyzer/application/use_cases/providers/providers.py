"""Provider administration: list configured providers and test their connection."""

from collections.abc import Mapping
from dataclasses import dataclass

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.market_data import MarketDataProvider
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """A configured provider as shown in Admin > Data Providers."""

    plugin_name: str
    kind: str
    display_name: str
    is_enabled: bool


class ProviderAdmin:
    """List providers and test connections through the registered plugins."""

    def __init__(
        self, uow_factory: UnitOfWorkFactory, plugins: Mapping[str, MarketDataProvider]
    ) -> None:
        """Use ``plugins`` (name → plugin instance) to run connection tests."""
        self._uow_factory = uow_factory
        self._plugins = plugins

    async def list_all(self) -> list[ProviderInfo]:
        """Return every configured provider."""
        async with self._uow_factory() as uow:
            rows = await uow.providers.list_all()
        return [ProviderInfo(*row) for row in rows]

    def test_connection(self, plugin_name: str) -> bool:
        """Return whether the plugin can reach its data source."""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise NotFoundError(f"provider {plugin_name} not found")
        return plugin.test_connection()
