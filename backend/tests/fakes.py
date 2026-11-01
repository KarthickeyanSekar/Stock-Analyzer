"""In-memory implementations of the repository ports, for fast tests without a database."""

import math
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime
from types import TracebackType
from typing import Self

from stock_analyzer.application.ports.ml import Analog
from stock_analyzer.domain.analysis.features import Features, embedding
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.journal.progress import PlanProgress
from stock_analyzer.domain.journal.settings import JournalSettings
from stock_analyzer.domain.journal.trade_plan import TradePlan
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.labels import Label
from stock_analyzer.domain.prediction.model_version import ModelStatus, ModelVersion
from stock_analyzer.domain.prediction.prediction import Prediction
from stock_analyzer.domain.pricing.candle import Candle
from stock_analyzer.domain.stock.stock import Stock


class InMemoryStore:
    """Shared state behind every fake unit of work (one 'database')."""

    def __init__(self) -> None:
        self.markets: dict[str, tuple[str, str, str]] = {}
        self.stocks: dict[int, Stock] = {}
        self.candles: dict[int, dict[date, Candle]] = {}
        self.quarters: dict[int, dict[date, QuarterlyFundamentals]] = {}
        self.predictions: dict[tuple[int, date, str, str], Prediction] = {}
        self.plans: dict[int, TradePlan] = {}
        self.snapshots: dict[int, dict[date, PlanProgress]] = {}
        self.settings: JournalSettings | None = None
        self.features: dict[tuple[str, int, date], Features] = {}
        self.labels: dict[tuple[str, int, date], Label] = {}
        self.models: list[ModelVersion] = []
        self.providers: dict[str, tuple[str, str, str, bool]] = {}
        self.credentials: dict[str, dict[str, tuple[bytes, str]]] = {}
        self.primary: dict[tuple[str, str], str] = {}


class FakeStocks:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def ensure_market(self, code: str, name: str, currency: str, timezone: str) -> None:
        self._s.markets.setdefault(code, (name, currency, timezone))

    async def upsert_many(self, stocks: Sequence[Stock]) -> list[Stock]:
        result = []
        for stock in stocks:
            existing = await self.get_by_symbol(stock.symbol, stock.exchange)
            stock_id = existing.id if existing else len(self._s.stocks) + 1
            self._s.stocks[stock_id or 0] = replace(stock, id=stock_id)
            result.append(self._s.stocks[stock_id or 0])
        return result

    async def search(self, query: str | None, limit: int) -> list[Stock]:
        needle = (query or "").lower()
        found = [
            s
            for s in sorted(self._s.stocks.values(), key=lambda s: s.symbol)
            if needle in s.symbol.lower() or needle in s.name.lower()
        ]
        return found[:limit]

    async def get_by_symbol(self, symbol: str, exchange: str = "NSE") -> Stock | None:
        return next(
            (s for s in self._s.stocks.values() if (s.symbol, s.exchange) == (symbol, exchange)),
            None,
        )

    async def get(self, stock_id: int) -> Stock | None:
        return self._s.stocks.get(stock_id)


class FakePrices:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def upsert_candles(
        self, stock_id: int, candles: Sequence[Candle], source_provider: str
    ) -> int:
        self._s.candles.setdefault(stock_id, {}).update({c.trade_date: c for c in candles})
        return len(candles)

    async def delete_by_source(self, source_provider: str) -> int:
        count = sum(len(c) for c in self._s.candles.values())
        self._s.candles.clear()  # the fake store holds a single (synthetic) source
        return count

    async def get_candles(
        self, stock_id: int, start: date | None = None, end: date | None = None
    ) -> list[Candle]:
        return [
            c
            for day, c in sorted(self._s.candles.get(stock_id, {}).items())
            if (start is None or day >= start) and (end is None or day <= end)
        ]


class FakeFundamentals:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def upsert_quarters(
        self, stock_id: int, quarters: Sequence[QuarterlyFundamentals], source_provider: str
    ) -> int:
        self._s.quarters.setdefault(stock_id, {}).update({q.period_end: q for q in quarters})
        return len(quarters)

    async def delete_by_source(self, source_provider: str) -> int:
        count = sum(len(q) for q in self._s.quarters.values())
        self._s.quarters.clear()
        return count

    async def list_quarters(
        self, stock_id: int, known_on: date | None = None
    ) -> list[QuarterlyFundamentals]:
        return [
            q
            for _, q in sorted(self._s.quarters.get(stock_id, {}).items())
            if known_on is None or q.is_known_on(known_on)
        ]


class FakePredictions:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def save_many(self, predictions: Sequence[Prediction], algorithm: str) -> int:
        for p in predictions:
            key = (p.stock_id, p.as_of, p.category.value, p.model_version)
            self._s.predictions[key] = replace(p, id=len(self._s.predictions) + 1)
        return len(predictions)

    async def latest_for_category(self, category: HoldingCategory) -> list[Prediction]:
        latest: dict[int, Prediction] = {}
        for p in self._s.predictions.values():
            if p.category is category and (
                p.stock_id not in latest or p.as_of > latest[p.stock_id].as_of
            ):
                latest[p.stock_id] = p
        return list(latest.values())

    async def latest_for_stock(self, stock_id: int) -> list[Prediction]:
        latest: dict[str, Prediction] = {}
        for p in self._s.predictions.values():
            if p.stock_id == stock_id and (
                p.category.value not in latest or p.as_of > latest[p.category.value].as_of
            ):
                latest[p.category.value] = p
        return list(latest.values())


class FakeTradePlans:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def add(self, plan: TradePlan) -> TradePlan:
        plan.id = len(self._s.plans) + 1
        self._s.plans[plan.id] = replace(plan)
        return plan

    async def get(self, plan_id: int) -> TradePlan | None:
        plan = self._s.plans.get(plan_id)
        return replace(plan) if plan else None

    async def list_all(self) -> list[TradePlan]:
        return [replace(p) for p in sorted(self._s.plans.values(), key=lambda p: -(p.id or 0))]

    async def update(self, plan: TradePlan) -> None:
        self._s.plans[plan.id or 0] = replace(plan)


class FakeProviders:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def ensure(self, plugin_name: str, kind: str, display_name: str) -> None:
        self._s.providers.setdefault(plugin_name, (plugin_name, kind, display_name, True))

    async def list_all(self) -> list[tuple[str, str, str, bool]]:
        return list(self._s.providers.values())

    async def set_credential(
        self, plugin_name: str, field: str, encrypted: bytes, last4: str
    ) -> None:
        self._s.credentials.setdefault(plugin_name, {})[field] = (encrypted, last4)

    async def delete_credentials(self, plugin_name: str) -> None:
        self._s.credentials.pop(plugin_name, None)

    async def credentials(self, plugin_name: str) -> dict[str, bytes]:
        return {f: v[0] for f, v in self._s.credentials.get(plugin_name, {}).items()}

    async def credential_hints(self, plugin_name: str) -> dict[str, str]:
        return {f: v[1] for f, v in self._s.credentials.get(plugin_name, {}).items()}

    async def set_primary(self, market_code: str, data_type: str, plugin_name: str) -> None:
        self._s.primary[(market_code, data_type)] = plugin_name

    async def primary(self, market_code: str, data_type: str) -> str | None:
        return self._s.primary.get((market_code, data_type))


class FakePlanStatuses:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def upsert_many(self, plan_id: int, snapshots: Sequence[PlanProgress]) -> int:
        self._s.snapshots.setdefault(plan_id, {}).update({s.as_of: s for s in snapshots})
        return len(snapshots)

    async def list_for_plan(self, plan_id: int) -> list[PlanProgress]:
        return [s for _, s in sorted(self._s.snapshots.get(plan_id, {}).items())]

    async def delete_all(self) -> int:
        count = sum(len(s) for s in self._s.snapshots.values())
        self._s.snapshots.clear()
        return count


class FakeSettings:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def get(self) -> JournalSettings:
        return self._s.settings or JournalSettings()

    async def save(self, settings: JournalSettings) -> None:
        self._s.settings = settings


class FakeFeatures:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def upsert_features(
        self, feature_set: str, rows: Sequence[tuple[int, date, Features]]
    ) -> int:
        self._s.features.update({(feature_set, s, d): f for s, d, f in rows})
        return len(rows)

    async def load_features(self, feature_set: str) -> dict[tuple[int, date], Features]:
        return {(s, d): f for (fs, s, d), f in self._s.features.items() if fs == feature_set}

    async def latest_features(self, feature_set: str) -> dict[int, tuple[date, Features]]:
        latest: dict[int, tuple[date, Features]] = {}
        for (s, d), f in sorted((await self.load_features(feature_set)).items()):
            latest[s] = (d, f)
        return latest

    async def upsert_labels(
        self, category: HoldingCategory, rows: Sequence[tuple[int, date, Label]]
    ) -> int:
        self._s.labels.update({(category.value, s, d): label for s, d, label in rows})
        return len(rows)

    async def load_labels(self, category: HoldingCategory) -> dict[tuple[int, date], Label]:
        return {(s, d): v for (c, s, d), v in self._s.labels.items() if c == category.value}

    async def nearest(
        self,
        feature_set: str,
        vector: Sequence[float],
        category: HoldingCategory,
        before: date,
        limit: int,
    ) -> list[Analog]:
        def distance(other: Sequence[float]) -> float:
            dot = sum(a * b for a, b in zip(vector, other, strict=True))
            norm = math.sqrt(sum(a * a for a in vector)) * math.sqrt(sum(b * b for b in other))
            return 1 - dot / norm if norm else 1.0

        found = [
            Analog(s, d, distance(embedding(f)), self._s.labels[(category.value, s, d)])
            for (fs, s, d), f in self._s.features.items()
            if fs == feature_set and d < before and (category.value, s, d) in self._s.labels
        ]
        return sorted(found, key=lambda a: a.distance)[:limit]

    async def delete_all(self) -> int:
        count = len(self._s.features) + len(self._s.labels)
        self._s.features.clear()
        self._s.labels.clear()
        return count


class FakeModels:
    def __init__(self, store: InMemoryStore) -> None:
        self._s = store

    async def add(self, version: ModelVersion) -> ModelVersion:
        version.id = len(self._s.models) + 1
        self._s.models.append(version)
        return version

    async def active(self, category: HoldingCategory) -> ModelVersion | None:
        return next(
            (
                m
                for m in self._s.models
                if m.category is category and m.status is ModelStatus.ACTIVE
            ),
            None,
        )

    async def activate(self, version_id: int, now: datetime) -> None:
        target = next(m for m in self._s.models if m.id == version_id)
        for m in self._s.models:
            if m.category is target.category and m.status is ModelStatus.ACTIVE:
                m.status = ModelStatus.RETIRED
        target.status, target.activated_at = ModelStatus.ACTIVE, now

    async def rollback(self, category: HoldingCategory, now: datetime) -> ModelVersion | None:
        retired = [
            m
            for m in self._s.models
            if m.category is category and m.status is ModelStatus.RETIRED and m.activated_at
        ]
        if not retired:
            return None
        previous = max(retired, key=lambda m: m.activated_at or now)
        current = await self.active(category)
        if current:
            current.status = ModelStatus.RETIRED
        previous.status, previous.activated_at = ModelStatus.ACTIVE, now
        return previous

    async def list_for(self, category: HoldingCategory) -> list[ModelVersion]:
        return [m for m in reversed(self._s.models) if m.category is category]


class FakeUnitOfWork:
    """Writes go straight to the shared store (good enough for use-case and API tests)."""

    def __init__(self, store: InMemoryStore) -> None:
        self.stocks = FakeStocks(store)
        self.prices = FakePrices(store)
        self.fundamentals = FakeFundamentals(store)
        self.predictions = FakePredictions(store)
        self.trade_plans = FakeTradePlans(store)
        self.providers = FakeProviders(store)
        self.plan_statuses = FakePlanStatuses(store)
        self.settings = FakeSettings(store)
        self.features = FakeFeatures(store)
        self.models = FakeModels(store)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None
