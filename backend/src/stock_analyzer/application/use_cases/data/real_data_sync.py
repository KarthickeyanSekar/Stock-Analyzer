"""Per-stock real-data sync: an admin picks up to five stocks; a job loads their real prices.

Keeps API usage small while the provider is limited: only picked stocks are fetched, and only
their synthetic candles are replaced. Every other stock keeps its synthetic data.
"""

from dataclasses import dataclass
from datetime import date

from stock_analyzer.application.errors import ConfigurationError, NotFoundError, ProviderError
from stock_analyzer.application.ports.auth import AuditEntry
from stock_analyzer.application.ports.repositories import StockDataSource, UnitOfWorkFactory
from stock_analyzer.application.use_cases.data.switch_to_real_data import SYNTHETIC_SOURCE
from stock_analyzer.application.use_cases.providers.providers import ProviderAdmin
from stock_analyzer.domain.shared.errors import DomainError
from stock_analyzer.domain.users.user import User

MAX_REAL_SYNC_STOCKS = 5


class RealSyncLimitError(DomainError):
    """More stocks were picked than the sync allows."""


@dataclass(frozen=True, slots=True)
class StockSyncResult:
    """What the sync did for one stock (``error`` set when it failed)."""

    symbol: str
    candles: int
    error: str | None = None


class RealDataSync:
    """List data sources, pick stocks for the sync, and run it."""

    def __init__(self, uow_factory: UnitOfWorkFactory, providers: ProviderAdmin) -> None:
        """Fetch from the primary provider configured in ``providers``."""
        self._uow_factory = uow_factory
        self._providers = providers

    async def sources(self) -> list[StockDataSource]:
        """Every stock with where its prices come from and whether it is picked."""
        async with self._uow_factory() as uow:
            return await uow.stocks.data_sources()

    async def set_enabled(self, admin: User, symbol: str, *, is_enabled: bool) -> None:
        """Pick or unpick ``symbol``; at most ``MAX_REAL_SYNC_STOCKS`` may be picked."""
        async with self._uow_factory() as uow:
            stock = await uow.stocks.get_by_symbol(symbol)
            if stock is None or stock.id is None:
                raise NotFoundError(f"stock {symbol} not found")
            if is_enabled:
                picked = {s.id for s in await uow.stocks.real_sync_stocks()}
                if stock.id not in picked and len(picked) >= MAX_REAL_SYNC_STOCKS:
                    raise RealSyncLimitError(
                        f"at most {MAX_REAL_SYNC_STOCKS} stocks can sync real data; "
                        "turn one off first"
                    )
            await uow.stocks.set_real_sync(stock.id, is_enabled=is_enabled)
            await uow.audit.add(
                AuditEntry(
                    None,
                    admin.id,
                    "real_sync_enabled" if is_enabled else "real_sync_disabled",
                    {"symbol": stock.symbol},
                )
            )
            await uow.commit()

    async def sync(self, start: date, end: date) -> list[StockSyncResult]:
        """Load ``start``..``end`` candles for each picked stock from the primary provider."""
        provider = await self._providers.primary_provider()
        if provider.name == SYNTHETIC_SOURCE:
            raise ConfigurationError("make a real provider primary in Admin > Providers first")
        async with self._uow_factory() as uow:
            stocks = await uow.stocks.real_sync_stocks()
        results: list[StockSyncResult] = []
        for stock in stocks:
            if stock.id is None:  # pragma: no cover - stored stocks always have ids
                continue
            try:
                candles = provider.daily_candles(stock.symbol, start, end)
            except ProviderError as error:
                # One failing symbol must not stop the others (API limits are per call).
                results.append(StockSyncResult(stock.symbol, 0, str(error)))
                continue
            if not candles:
                results.append(StockSyncResult(stock.symbol, 0, "provider returned no candles"))
                continue
            async with self._uow_factory() as uow:
                await uow.prices.delete_for_stock(stock.id, SYNTHETIC_SOURCE)
                written = await uow.prices.upsert_candles(stock.id, candles, provider.name)
                await uow.stocks.set_source_provider(stock.id, provider.name)
                await uow.audit.add(
                    AuditEntry(
                        None,
                        None,
                        "real_sync_loaded",
                        {"symbol": stock.symbol, "provider": provider.name, "candles": written},
                    )
                )
                await uow.commit()
            results.append(StockSyncResult(stock.symbol, written))
        return results
