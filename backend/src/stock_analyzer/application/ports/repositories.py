"""Repository ports and the unit of work that groups them in one transaction."""

from collections.abc import Sequence
from datetime import date
from types import TracebackType
from typing import Protocol, Self

from stock_analyzer.application.ports.ml import FeatureRepository, ModelRegistry
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.journal.progress import PlanProgress
from stock_analyzer.domain.journal.settings import JournalSettings
from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.domain.prediction.prediction import Prediction
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock


class StockRepository(Protocol):
    """Stocks and their markets."""

    async def ensure_market(self, code: str, name: str, currency: str, timezone: str) -> None:
        """Create the market if it doesn't exist."""
        ...

    async def upsert_many(self, stocks: Sequence[Stock]) -> list[Stock]:
        """Insert or update stocks by (exchange, symbol) and return them with ids."""
        ...

    async def search(self, query: str | None, limit: int) -> list[Stock]:
        """Return active stocks whose symbol or name contains ``query``."""
        ...

    async def get_by_symbol(self, symbol: str, exchange: str = "NSE") -> Stock | None:
        """Return one stock, or ``None``."""
        ...

    async def get(self, stock_id: int) -> Stock | None:
        """Return one stock by id, or ``None``."""
        ...


class PriceRepository(Protocol):
    """Daily candles."""

    async def upsert_candles(
        self, stock_id: int, candles: Sequence[Candle], source_provider: str
    ) -> int:
        """Insert or replace candles; return how many were written."""
        ...

    async def get_candles(
        self, stock_id: int, start: date | None = None, end: date | None = None
    ) -> list[Candle]:
        """Return candles in date order."""
        ...


class FundamentalsRepository(Protocol):
    """Quarterly fundamentals."""

    async def upsert_quarters(
        self, stock_id: int, quarters: Sequence[QuarterlyFundamentals], source_provider: str
    ) -> int:
        """Insert or replace quarters by period end; return how many were written."""
        ...

    async def list_quarters(
        self, stock_id: int, known_on: date | None = None
    ) -> list[QuarterlyFundamentals]:
        """Return quarters in period order; with ``known_on``, only those announced by then."""
        ...


class PredictionRepository(Protocol):
    """Predictions and the model versions that made them."""

    async def save_many(self, predictions: Sequence[Prediction], algorithm: str) -> int:
        """Replace predictions for the same stock, date, category and model; return count."""
        ...

    async def latest_for_stock(self, stock_id: int) -> list[Prediction]:
        """Return the newest prediction per holding category."""
        ...


class TradePlanRepository(Protocol):
    """Trade journal plans."""

    async def add(self, plan: TradePlan) -> TradePlan:
        """Store a new plan and return it with its id."""
        ...

    async def get(self, plan_id: int) -> TradePlan | None:
        """Return one plan, or ``None``."""
        ...

    async def list_all(self) -> list[TradePlan]:
        """Return every plan, newest first."""
        ...

    async def update(self, plan: TradePlan) -> None:
        """Persist changes to an existing plan."""
        ...


class PlanStatusRepository(Protocol):
    """Daily tracking snapshots of plans (``plan_daily_status``)."""

    async def upsert_many(self, plan_id: int, snapshots: Sequence[PlanProgress]) -> int:
        """Insert or replace one snapshot per trading day; return how many were written."""
        ...

    async def list_for_plan(self, plan_id: int) -> list[PlanProgress]:
        """Return the plan's snapshots in date order."""
        ...


class SettingsRepository(Protocol):
    """The app-wide journal settings record (Q63)."""

    async def get(self) -> JournalSettings:
        """Return the settings, or the defaults when none are saved yet."""
        ...

    async def save(self, settings: JournalSettings) -> None:
        """Create or replace the settings record."""
        ...


class ProviderRepository(Protocol):
    """Configured provider plugins."""

    async def ensure(self, plugin_name: str, kind: str, display_name: str) -> None:
        """Register the provider if it isn't configured yet."""
        ...

    async def list_all(self) -> list[tuple[str, str, str, bool]]:
        """Return ``(plugin_name, kind, display_name, is_enabled)`` for every provider."""
        ...


class UnitOfWork(Protocol):
    """One database transaction; use as ``async with uow: ... await uow.commit()``."""

    @property
    def stocks(self) -> StockRepository:
        """Stock repository bound to this transaction."""
        ...

    @property
    def prices(self) -> PriceRepository:
        """Price repository bound to this transaction."""
        ...

    @property
    def fundamentals(self) -> FundamentalsRepository:
        """Fundamentals repository bound to this transaction."""
        ...

    @property
    def predictions(self) -> PredictionRepository:
        """Prediction repository bound to this transaction."""
        ...

    @property
    def trade_plans(self) -> TradePlanRepository:
        """Trade plan repository bound to this transaction."""
        ...

    @property
    def providers(self) -> ProviderRepository:
        """Provider repository bound to this transaction."""
        ...

    @property
    def features(self) -> FeatureRepository:
        """Feature store and labels bound to this transaction."""
        ...

    @property
    def models(self) -> ModelRegistry:
        """Model registry bound to this transaction."""
        ...

    @property
    def plan_statuses(self) -> PlanStatusRepository:
        """Plan tracking snapshots bound to this transaction."""
        ...

    @property
    def settings(self) -> SettingsRepository:
        """Journal settings bound to this transaction."""
        ...

    async def __aenter__(self) -> Self:
        """Start the transaction."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Roll back anything not committed."""
        ...

    async def commit(self) -> None:
        """Commit the transaction."""
        ...


class UnitOfWorkFactory(Protocol):
    """Creates a fresh unit of work per request or job."""

    def __call__(self) -> UnitOfWork:
        """Return a new unit of work."""
        ...
