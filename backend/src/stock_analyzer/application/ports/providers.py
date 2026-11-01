"""Provider plugin catalog port: which plugins exist and how to build one with credentials."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from stock_analyzer.application.ports.fundamentals import FundamentalsProvider
from stock_analyzer.application.ports.market_data import MarketDataProvider


class DataProvider(MarketDataProvider, FundamentalsProvider, Protocol):
    """A plugin that supplies both prices and fundamentals (mock, EODHD)."""


@dataclass(frozen=True, slots=True)
class PluginInfo:
    """Static description of a plugin."""

    name: str
    display_name: str
    credential_fields: tuple[str, ...]
    is_synthetic: bool


class PluginCatalog(Protocol):
    """Known plugins (code), independent of what is configured in the database."""

    def plugins(self) -> list[PluginInfo]:
        """Every available plugin."""
        ...

    def create(self, name: str, credentials: Mapping[str, str]) -> DataProvider:
        """Build a plugin instance with decrypted credentials."""
        ...
