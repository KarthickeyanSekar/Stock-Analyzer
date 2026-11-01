"""Composition root: builds and wires every dependency in one place."""

from dataclasses import dataclass
from functools import partial

from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.application.ports.fundamentals import FundamentalsProvider
from stock_analyzer.application.ports.market_data import MarketDataProvider
from stock_analyzer.application.ports.ml import ModelTrainer
from stock_analyzer.application.ports.providers import PluginCatalog
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.application.ports.security import SecretCipher
from stock_analyzer.application.use_cases.journal.settings import JournalSettingsService
from stock_analyzer.application.use_cases.journal.trade_plans import TradePlanService
from stock_analyzer.application.use_cases.providers.providers import ProviderAdmin
from stock_analyzer.application.use_cases.screener.queries import ScreenerQueries
from stock_analyzer.application.use_cases.stocks.queries import StockQueries
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.infrastructure.config.settings import Settings, get_settings
from stock_analyzer.infrastructure.logging.setup import configure_logging
from stock_analyzer.infrastructure.ml.lightgbm_trainer import LightGbmTrainer
from stock_analyzer.infrastructure.persistence.database import (
    create_engine,
    create_session_factory,
)
from stock_analyzer.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from stock_analyzer.infrastructure.providers.catalog import StaticPluginCatalog
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider
from stock_analyzer.infrastructure.providers.mock.universe import SAMPLE_HOLIDAYS
from stock_analyzer.infrastructure.security.fernet_cipher import FernetCipher
from stock_analyzer.infrastructure.telemetry.setup import configure_telemetry
from stock_analyzer.infrastructure.time.system_clock import SystemClock


@dataclass(frozen=True)
class Container:
    """Wired application dependencies."""

    settings: Settings
    clock: Clock
    uow_factory: UnitOfWorkFactory
    calendar: TradingCalendar
    market_data: MarketDataProvider
    fundamentals: FundamentalsProvider
    catalog: PluginCatalog
    cipher: SecretCipher
    trainer: ModelTrainer

    @property
    def stock_queries(self) -> StockQueries:
        """Stock search, prices and predictions."""
        return StockQueries(self.uow_factory)

    @property
    def screener(self) -> ScreenerQueries:
        """Holding-period screener and similar past setups."""
        return ScreenerQueries(self.uow_factory)

    @property
    def trade_plans(self) -> TradePlanService:
        """Trade journal use cases."""
        return TradePlanService(self.uow_factory, self.calendar)

    @property
    def journal_settings(self) -> JournalSettingsService:
        """Journal defaults (Settings page)."""
        return JournalSettingsService(self.uow_factory)

    @property
    def provider_admin(self) -> ProviderAdmin:
        """Admin > Data Providers use cases."""
        return ProviderAdmin(self.uow_factory, self.catalog, self.cipher)


def build_container(settings: Settings | None = None) -> Container:
    """Create the dependency container for the running process."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    configure_telemetry(settings)
    session_factory = create_session_factory(create_engine(settings.database_url))
    # POC: the mock provider supplies prices and fundamentals; real plugins join the registry later.
    market_data = MockMarketDataProvider()
    return Container(
        settings=settings,
        clock=SystemClock(),
        uow_factory=partial(SqlAlchemyUnitOfWork, session_factory),
        calendar=TradingCalendar(SAMPLE_HOLIDAYS),
        market_data=market_data,
        fundamentals=market_data,
        catalog=StaticPluginCatalog(market_data),
        cipher=FernetCipher(settings.master_key.get_secret_value()),
        trainer=LightGbmTrainer(),
    )
