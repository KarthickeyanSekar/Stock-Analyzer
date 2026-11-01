"""Integration tests run against a throwaway PostgreSQL + TimescaleDB (``make test``).

They are skipped when ``SA_TEST_DATABASE_URL`` is unset (e.g., a plain local pytest run).
The schema is rebuilt from the Alembic migrations once per session.
"""

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import date
from functools import partial
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from stock_analyzer.application.use_cases.data.backfill_fundamentals import BackfillFundamentals
from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.prediction.run_baseline_predictions import (
    RunBaselinePredictions,
)
from stock_analyzer.infrastructure.persistence.database import (
    create_engine,
    create_session_factory,
)
from stock_analyzer.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider

DATABASE_URL = os.environ.get("SA_TEST_DATABASE_URL", "")
BACKEND_DIR = Path(__file__).resolve().parents[2]
SEED_START = date(2024, 1, 1)
SEED_END = date(2026, 10, 30)

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="SA_TEST_DATABASE_URL not set")


def alembic(*args: str) -> str:
    """Run an Alembic command against the test database and return its output."""
    result = subprocess.run(  # noqa: S603 - fixed command, test-only
        ["alembic", *args],  # noqa: S607
        cwd=BACKEND_DIR,
        env=os.environ | {"SA_DATABASE_URL": DATABASE_URL},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout + result.stderr


@pytest.fixture(scope="session")
def migrated() -> None:
    """Rebuild the schema from scratch once per session."""
    if not DATABASE_URL:
        pytest.skip("SA_TEST_DATABASE_URL not set")
    alembic("downgrade", "base")
    alembic("upgrade", "head")


@pytest.fixture
async def engine(migrated: None) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Empty tables before each test so tests don't depend on each other."""
    async with engine.begin() as connection:
        tables = await connection.scalars(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        names = ", ".join(f'"{name}"' for name in tables if name != "alembic_version")
        await connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield create_session_factory(engine)


@pytest.fixture
def uow_factory(session_factory: async_sessionmaker[AsyncSession]) -> partial[SqlAlchemyUnitOfWork]:
    return partial(SqlAlchemyUnitOfWork, session_factory)


@pytest.fixture
async def seeded(uow_factory: partial[SqlAlchemyUnitOfWork]) -> partial[SqlAlchemyUnitOfWork]:
    """Two years of synthetic data, fundamentals and predictions in the real database."""
    provider = MockMarketDataProvider(start=SEED_START, end=SEED_END)
    await BackfillPrices(uow_factory, provider).execute(SEED_START, SEED_END)
    await BackfillFundamentals(uow_factory, provider).execute(SEED_START, SEED_END)
    await RunBaselinePredictions(uow_factory).execute()
    return uow_factory
