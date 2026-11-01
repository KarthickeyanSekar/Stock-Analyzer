"""Plugin catalog: every provider plugin this build knows (implements ``PluginCatalog``)."""

import time
from collections.abc import Callable, Mapping

import httpx

from stock_analyzer.application.errors import NotFoundError
from stock_analyzer.application.ports.providers import DataProvider, PluginInfo
from stock_analyzer.infrastructure.providers.eodhd.provider import EodhdProvider
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider

Factory = Callable[[Mapping[str, str]], DataProvider]


def _no_wait(_seconds: float) -> None:
    """No back-off pauses when replaying recorded responses."""


class StaticPluginCatalog:
    """Plugins registered in code; credentials come from the database at call time."""

    def __init__(
        self,
        mock: MockMarketDataProvider | None = None,
        eodhd_client: httpx.Client | None = None,
    ) -> None:
        """Reuse ``mock`` (it caches data); ``eodhd_client`` lets tests replay HTTP fixtures."""
        mock_instance = mock or MockMarketDataProvider()
        self._entries: dict[str, tuple[PluginInfo, Factory]] = {
            "mock": (
                PluginInfo("mock", "Mock (synthetic data)", (), is_synthetic=True),
                lambda _credentials: mock_instance,
            ),
            "eodhd": (
                PluginInfo("eodhd", "EODHD", ("api_token",), is_synthetic=False),
                lambda credentials: EodhdProvider(
                    credentials.get("api_token", ""),
                    client=eodhd_client,
                    sleep=_no_wait if eodhd_client else time.sleep,
                ),
            ),
        }

    def plugins(self) -> list[PluginInfo]:
        """Every available plugin."""
        return [info for info, _ in self._entries.values()]

    def create(self, name: str, credentials: Mapping[str, str]) -> DataProvider:
        """Build the plugin with decrypted credentials."""
        if name not in self._entries:
            raise NotFoundError(f"provider {name} not found")
        return self._entries[name][1](credentials)
