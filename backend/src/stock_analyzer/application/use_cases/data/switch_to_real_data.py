"""Replace the synthetic POC data with data from the primary (real) provider.

Deletes synthetic prices and fundamentals plus every derived feature, label and plan snapshot,
then backfills from the primary provider. Journal plans and stored predictions are kept: plans
keep the prediction locked when they started. Run ``make features train predict track`` after.
"""

from dataclasses import dataclass
from datetime import date

from stock_analyzer.application.errors import ConfigurationError
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.application.use_cases.data.backfill_fundamentals import BackfillFundamentals
from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.providers.providers import ProviderAdmin

SYNTHETIC_SOURCE = "mock"


@dataclass(frozen=True, slots=True)
class SwitchResult:
    """What was removed and loaded."""

    provider: str
    deleted_candles: int
    deleted_quarters: int
    deleted_derived: int
    stocks: int
    candles: int
    quarters: int


class SwitchToRealData:
    """One-way switch from synthetic to real data (asks for confirmation in ``make``)."""

    def __init__(self, uow_factory: UnitOfWorkFactory, providers: ProviderAdmin) -> None:
        """Use the primary provider configured in ``providers``."""
        self._uow_factory = uow_factory
        self._providers = providers

    async def execute(self, start: date, end: date) -> SwitchResult:
        """Delete synthetic data and backfill ``start``..``end`` from the primary provider."""
        provider = await self._providers.primary_provider()
        if provider.name == SYNTHETIC_SOURCE:
            raise ConfigurationError("make a real provider primary in Admin > Providers first")
        # Fail before deleting anything if the provider can't be reached.
        check = provider.test_connection()
        if not check.is_ok:
            raise ConfigurationError(check.message)
        async with self._uow_factory() as uow:
            candles = await uow.prices.delete_by_source(SYNTHETIC_SOURCE)
            quarters = await uow.fundamentals.delete_by_source(SYNTHETIC_SOURCE)
            derived = await uow.features.delete_all() + await uow.plan_statuses.delete_all()
            await uow.commit()
        loaded = await BackfillPrices(self._uow_factory, provider).execute(start, end)
        loaded_quarters = await BackfillFundamentals(self._uow_factory, provider).execute(
            start, end
        )
        return SwitchResult(
            provider=provider.name,
            deleted_candles=candles,
            deleted_quarters=quarters,
            deleted_derived=derived,
            stocks=loaded.stocks,
            candles=loaded.candles,
            quarters=loaded_quarters,
        )
