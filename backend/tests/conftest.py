import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from stock_analyzer.application.use_cases.data.backfill_fundamentals import BackfillFundamentals
from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.prediction.run_baseline_predictions import (
    RunBaselinePredictions,
)
from stock_analyzer.bootstrap import Container
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.infrastructure.config.settings import Environment, Settings
from stock_analyzer.infrastructure.ml.lightgbm_trainer import LightGbmTrainer
from stock_analyzer.infrastructure.providers.catalog import StaticPluginCatalog
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider
from stock_analyzer.infrastructure.providers.mock.universe import SAMPLE_HOLIDAYS
from stock_analyzer.infrastructure.security.fernet_cipher import FernetCipher
from stock_analyzer.main import create_app
from tests.eodhd_fixtures import client as eodhd_client
from tests.fakes import FakeUnitOfWork, InMemoryStore

# A fresh Fernet key per test run (never stored anywhere).
TEST_MASTER_KEY = Fernet.generate_key().decode()
ADMIN_EMAIL = "admin@test.local"
FIXED_NOW = datetime(2026, 1, 2, 9, 15, tzinfo=UTC)
SEED_START = date(2024, 1, 1)
SEED_END = date(2026, 10, 30)


class FixedClock:
    def now(self) -> datetime:
        return FIXED_NOW


def make_container(store: InMemoryStore) -> Container:
    provider = MockMarketDataProvider(start=SEED_START, end=SEED_END)
    return Container(
        settings=Settings(env=Environment.TEST, dev_login=True, admin_emails=ADMIN_EMAIL),
        clock=FixedClock(),
        uow_factory=lambda: FakeUnitOfWork(store),
        calendar=TradingCalendar(SAMPLE_HOLIDAYS),
        market_data=provider,
        fundamentals=provider,
        catalog=StaticPluginCatalog(provider, eodhd_client=eodhd_client()),
        cipher=FernetCipher(TEST_MASTER_KEY),
        trainer=LightGbmTrainer(rounds=30),
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


def sign_in(client: TestClient, email: str = ADMIN_EMAIL, invite_code: str | None = None) -> None:
    """Sign the test client in with the dev sign-in (the cookie stays on the client)."""
    response = client.post("/api/auth/dev-login", json={"email": email, "invite_code": invite_code})
    assert response.status_code == 200, response.text


@pytest.fixture
def anonymous_client() -> Iterator[TestClient]:
    with TestClient(create_app(make_container(InMemoryStore()))) as test_client:
        yield test_client


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(make_container(InMemoryStore()))) as test_client:
        sign_in(test_client)
        yield test_client


@pytest.fixture
def seeded_client(seeded_store: InMemoryStore) -> Iterator[TestClient]:
    with TestClient(create_app(make_container(seeded_store))) as test_client:
        sign_in(test_client)
        yield test_client
