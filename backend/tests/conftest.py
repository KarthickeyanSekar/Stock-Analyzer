import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from stock_analyzer.application.use_cases.data.backfill_fundamentals import BackfillFundamentals
from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.prediction.run_baseline_predictions import (
    RunBaselinePredictions,
)
from stock_analyzer.bootstrap import Container
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.infrastructure.config.settings import Environment, Settings
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider
from stock_analyzer.infrastructure.providers.mock.universe import SAMPLE_HOLIDAYS
from stock_analyzer.main import create_app
from tests.fakes import FakeUnitOfWork, InMemoryStore

FIXED_NOW = datetime(2026, 1, 2, 9, 15, tzinfo=UTC)
SEED_START = date(2024, 1, 1)
SEED_END = date(2026, 10, 30)


class FixedClock:
    def now(self) -> datetime:
        return FIXED_NOW


def make_container(store: InMemoryStore) -> Container:
    provider = MockMarketDataProvider(start=SEED_START, end=SEED_END)
    return Container(
        settings=Settings(env=Environment.TEST),
        clock=FixedClock(),
        uow_factory=lambda: FakeUnitOfWork(store),
        calendar=TradingCalendar(SAMPLE_HOLIDAYS),
        market_data=provider,
        fundamentals=provider,
        plugins={provider.name: provider},
    )


@pytest.fixture(scope="session")
def seeded_store() -> InMemoryStore:
    """Synthetic data loaded and predicted once per test session (in memory)."""
    store = InMemoryStore()
    container = make_container(store)

    async def seed() -> None:
        await BackfillPrices(container.uow_factory, container.market_data).execute(
            SEED_START, SEED_END
        )
        await BackfillFundamentals(container.uow_factory, container.fundamentals).execute(
            SEED_START, SEED_END
        )
        await RunBaselinePredictions(container.uow_factory).execute()

    asyncio.run(seed())
    return store


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(make_container(InMemoryStore()))) as test_client:
        yield test_client


@pytest.fixture
def seeded_client(seeded_store: InMemoryStore) -> Iterator[TestClient]:
    with TestClient(create_app(make_container(seeded_store))) as test_client:
        yield test_client
