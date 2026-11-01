"""Schema, migrations and SQLAlchemy repositories against a real PostgreSQL + TimescaleDB."""

from datetime import date
from decimal import Decimal
from functools import partial

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.journal.trade_plans import (
    CloseTradePlanRequest,
    CreateTradePlanRequest,
    TradePlanService,
)
from stock_analyzer.domain.journal.trade_plan import PlanOutcome, PlanStatus
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from stock_analyzer.infrastructure.providers.mock.provider import MockMarketDataProvider
from stock_analyzer.infrastructure.providers.mock.universe import SAMPLE_HOLIDAYS
from tests.integration.conftest import DATABASE_URL, SEED_END, SEED_START, alembic

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="SA_TEST_DATABASE_URL not set")
UowFactory = partial[SqlAlchemyUnitOfWork]


def test_migrations_round_trip_without_drift(migrated: None) -> None:
    alembic("downgrade", "base")
    alembic("upgrade", "head")

    assert "No new upgrade operations detected" in alembic("check")


async def test_prices_daily_is_a_hypertable(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        tables = await connection.scalars(
            text("SELECT hypertable_name FROM timescaledb_information.hypertables")
        )
        assert "prices_daily" in set(tables)


async def test_backfill_is_idempotent(uow_factory: UowFactory, engine: AsyncEngine) -> None:
    provider = MockMarketDataProvider(start=SEED_START, end=SEED_END)
    backfill = BackfillPrices(uow_factory, provider)

    first = await backfill.execute(date(2026, 1, 1), SEED_END)
    second = await backfill.execute(date(2026, 1, 1), SEED_END)

    async with engine.connect() as connection:
        rows = await connection.scalar(text("SELECT count(*) FROM prices_daily"))
        non_mock = await connection.scalar(
            text("SELECT count(*) FROM prices_daily WHERE source_provider <> 'mock'")
        )
    assert first == second
    assert rows == first.candles
    assert non_mock == 0


async def test_candles_and_stocks_round_trip(seeded: UowFactory) -> None:
    async with seeded() as uow:
        stock = await uow.stocks.get_by_symbol("INFY")
        assert stock is not None and stock.id is not None
        candles = await uow.prices.get_candles(stock.id, date(2026, 10, 1), SEED_END)

    expected = MockMarketDataProvider(start=SEED_START, end=SEED_END).daily_candles(
        "INFY", date(2026, 10, 1), SEED_END
    )
    assert candles == list(expected)  # Decimal prices survive NUMERIC exactly
    assert (stock.market_code, stock.currency, stock.timezone) == ("IN", "INR", "Asia/Kolkata")


async def test_fundamentals_are_exact_and_point_in_time(seeded: UowFactory) -> None:
    async with seeded() as uow:
        stock = await uow.stocks.get_by_symbol("TCS")
        assert stock is not None and stock.id is not None
        everything = await uow.fundamentals.list_quarters(stock.id)
        known = await uow.fundamentals.list_quarters(stock.id, known_on=date(2025, 1, 1))

    expected = MockMarketDataProvider(start=SEED_START, end=SEED_END).quarterly_fundamentals(
        "TCS", SEED_START, SEED_END
    )
    assert everything == list(expected)
    assert known and len(known) < len(everything)
    assert all(q.announced_date <= date(2025, 1, 1) for q in known)


async def test_predictions_latest_per_category(seeded: UowFactory) -> None:
    async with seeded() as uow:
        stock = await uow.stocks.get_by_symbol("RELIANCE")
        assert stock is not None and stock.id is not None
        predictions = await uow.predictions.latest_for_stock(stock.id)

    # ~2 years of seed data: every category up to 2Y has enough history, 3Y doesn't
    assert {p.category for p in predictions} == set(HoldingCategory) - {HoldingCategory.Y3}
    assert all(p.range.p10_pct <= p.range.p50_pct <= p.range.p90_pct for p in predictions)


async def test_trade_plan_lifecycle_is_persisted(seeded: UowFactory) -> None:
    service = TradePlanService(seeded, TradingCalendar(SAMPLE_HOLIDAYS))
    plan = await service.create(
        CreateTradePlanRequest(
            symbol="INFY",
            category=HoldingCategory.D50,
            start_date=date(2026, 10, 30),
            target_pct=Decimal("10"),
        )
    )
    assert plan.id is not None

    closed = await service.close(
        CloseTradePlanRequest(
            plan_id=plan.id,
            exit_date=date(2026, 12, 30),
            exit_price=plan.entry_price * Decimal("1.1"),
        )
    )
    reloaded = await service.get(plan.id)

    assert closed.outcome is PlanOutcome.SUCCESS
    assert reloaded.status is PlanStatus.CLOSED
    assert reloaded.outcome is PlanOutcome.SUCCESS
    assert reloaded.target_pct == Decimal("10")
    assert [p.id for p in await service.list_all()] == [plan.id]
