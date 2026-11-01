"""Provider administration: credentials (encrypted), connection tests and the primary provider.

Secrets go in, never out: listings show only the last 4 characters of each credential.
"""

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field

from stock_analyzer.application.errors import ConfigurationError, NotFoundError
from stock_analyzer.application.ports.market_data import ConnectionCheck
from stock_analyzer.application.ports.providers import DataProvider, PluginCatalog, PluginInfo
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.application.ports.security import SecretCipher

MARKET = "IN"
DATA_TYPES = ("MARKET_DATA", "FUNDAMENTALS")
DEFAULT_PROVIDER = "mock"
MIN_SECRET_LENGTH = 8


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """A provider as shown in Admin > Data Providers."""

    plugin_name: str
    kind: str
    display_name: str
    is_enabled: bool
    is_synthetic: bool = True
    is_primary: bool = False
    credential_fields: tuple[str, ...] = ()
    # {field: last 4 characters} for fields that are set
    credential_hints: dict[str, str] = field(default_factory=dict)

    @property
    def has_credentials(self) -> bool:
        """Whether every required credential field is set."""
        return all(f in self.credential_hints for f in self.credential_fields)


class ProviderAdmin:
    """Configure providers; build the primary one for data jobs."""

    def __init__(
        self, uow_factory: UnitOfWorkFactory, catalog: PluginCatalog, cipher: SecretCipher
    ) -> None:
        """Use ``catalog`` to build plugins and ``cipher`` for credentials at rest."""
        self._uow_factory = uow_factory
        self._catalog = catalog
        self._cipher = cipher

    def _info(self, plugin_name: str) -> PluginInfo:
        info = next((p for p in self._catalog.plugins() if p.name == plugin_name), None)
        if info is None:
            raise NotFoundError(f"provider {plugin_name} not found")
        return info

    async def list_all(self) -> list[ProviderInfo]:
        """Every known plugin (registered on first listing) with masked credentials."""
        async with self._uow_factory() as uow:
            for plugin in self._catalog.plugins():
                await uow.providers.ensure(plugin.name, "MARKET_DATA", plugin.display_name)
            await uow.commit()
            primary = await uow.providers.primary(MARKET, DATA_TYPES[0]) or DEFAULT_PROVIDER
            result = []
            for name, kind, display, enabled in await uow.providers.list_all():
                info = next((p for p in self._catalog.plugins() if p.name == name), None)
                result.append(
                    ProviderInfo(
                        plugin_name=name,
                        kind=kind,
                        display_name=display,
                        is_enabled=enabled,
                        is_synthetic=info.is_synthetic if info else False,
                        is_primary=name == primary,
                        credential_fields=info.credential_fields if info else (),
                        credential_hints=await uow.providers.credential_hints(name),
                    )
                )
        return result

    async def save_credentials(self, plugin_name: str, values: Mapping[str, str]) -> None:
        """Encrypt and store credential fields (unknown or too-short values are rejected)."""
        info = self._info(plugin_name)
        unknown = set(values) - set(info.credential_fields)
        if unknown or not values:
            raise ConfigurationError(f"{plugin_name} expects {', '.join(info.credential_fields)}")
        if any(len(v.strip()) < MIN_SECRET_LENGTH for v in values.values()):
            raise ConfigurationError("credential looks too short; paste the full value")
        if not self._cipher.is_configured:
            raise ConfigurationError("SA_MASTER_KEY is not set: run `make bootstrap` first")
        async with self._uow_factory() as uow:
            await uow.providers.ensure(plugin_name, "MARKET_DATA", info.display_name)
            for name, value in values.items():
                secret = value.strip()
                await uow.providers.set_credential(
                    plugin_name, name, self._cipher.encrypt(secret), secret[-4:]
                )
            await uow.commit()

    async def delete_credentials(self, plugin_name: str) -> None:
        """Remove the credentials (not allowed while the provider is primary)."""
        self._info(plugin_name)
        async with self._uow_factory() as uow:
            if await uow.providers.primary(MARKET, DATA_TYPES[0]) == plugin_name:
                raise ConfigurationError("choose another primary provider before removing the key")
            await uow.providers.delete_credentials(plugin_name)
            await uow.commit()

    async def _build(self, plugin_name: str) -> DataProvider:
        info = self._info(plugin_name)
        async with self._uow_factory() as uow:
            encrypted = (
                await uow.providers.credentials(plugin_name) if info.credential_fields else {}
            )
        missing = [f for f in info.credential_fields if f not in encrypted]
        if missing:
            raise ConfigurationError(f"{info.display_name}: add the {', '.join(missing)} first")
        return self._catalog.create(
            plugin_name, {k: self._cipher.decrypt(v) for k, v in encrypted.items()}
        )

    async def test_connection(self, plugin_name: str) -> ConnectionCheck:
        """Check the provider with its stored credentials (network call off the event loop)."""
        try:
            provider = await self._build(plugin_name)
        except ConfigurationError as error:
            return ConnectionCheck(is_ok=False, message=str(error))
        return await asyncio.to_thread(provider.test_connection)

    async def set_primary(self, plugin_name: str) -> None:
        """Make the provider primary for prices and fundamentals (credentials must be set)."""
        await self._build(plugin_name)
        async with self._uow_factory() as uow:
            for data_type in DATA_TYPES:
                await uow.providers.set_primary(MARKET, data_type, plugin_name)
            await uow.commit()

    async def primary_provider(self) -> DataProvider:
        """The provider data jobs should use (mock until another one is made primary)."""
        async with self._uow_factory() as uow:
            name = await uow.providers.primary(MARKET, DATA_TYPES[0])
        return await self._build(name or DEFAULT_PROVIDER)
