"""Schema, migrations and SQLAlchemy repositories against a real PostgreSQL + TimescaleDB."""

import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import partial

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from stock_analyzer.application.use_cases.data.backfill_prices import BackfillPrices
from stock_analyzer.application.use_cases.journal.track_active_plans import TrackActivePlans
from stock_analyzer.application.use_cases.journal.trade_plans import (
    CloseTradePlanRequest,
    CreateTradePlanRequest,
    TradePlanService,
)
from stock_analyzer.application.use_cases.ml.build_features import BuildFeaturesAndLabels
from stock_analyzer.application.use_cases.screener.queries import ScreenerQueries
from stock_analyzer.domain.analysis.features import FEATURE_SET_VERSION, embedding
from stock_analyzer.domain.journal.progress import track
from stock_analyzer.domain.journal.settings import JournalSettings
from stock_analyzer.domain.journal.trade_plan import PlanOutcome, PlanStatus
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.prediction.model_version import ModelVersion
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS
from stock_analyzer.domain.prediction.screening import ScreenCriteria
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
            exit_price=plan.benchmark_price,  # judged against the locked prediction (Q31)
        )
    )
    reloaded = await service.get(plan.id)

    assert closed.outcome is PlanOutcome.SUCCESS
    assert reloaded.status is PlanStatus.CLOSED
    assert reloaded.outcome is PlanOutcome.SUCCESS
    assert reloaded.target_pct == Decimal("10")
    assert reloaded.predicted_pct == plan.predicted_pct is not None
    assert [p.id for p in await service.list_all()] == [plan.id]


async def test_settings_round_trip(uow_factory: UowFactory) -> None:
    async with uow_factory() as uow:
        assert await uow.settings.get() == JournalSettings()  # defaults before any save
        await uow.settings.save(JournalSettings(paper_capital=Decimal("250000.50")))
        await uow.commit()

    async with uow_factory() as uow:
        assert (await uow.settings.get()).paper_capital == Decimal("250000.50")


async def test_tracking_job_is_idempotent_and_point_in_time(
    seeded: UowFactory, engine: AsyncEngine
) -> None:
    calendar = TradingCalendar(SAMPLE_HOLIDAYS)
    plan = await TradePlanService(seeded, calendar).create(
        CreateTradePlanRequest(
            symbol="INFY",
            category=HoldingCategory.Y1,
            start_date=date(2026, 6, 1),
            target_pct=Decimal(15),
        )
    )
    assert plan.id is not None
    assert plan.reference_close == plan.entry_price and plan.predicted_pct is not None

    first = await TrackActivePlans(seeded, calendar).execute()
    second = await TrackActivePlans(seeded, calendar).execute()

    async with seeded() as uow:
        snapshots = await uow.plan_statuses.list_for_plan(plan.id)
        candles = await uow.prices.get_candles(plan.stock_id, plan.start_date)
        reloaded = await uow.trade_plans.get(plan.id)
    assert first == second == len(snapshots) == len(candles)
    assert [s.day_number for s in snapshots] == list(range(len(snapshots)))
    # Each snapshot equals tracking with only that day's history (no future data).
    for snapshot in snapshots[::20]:
        past = [c for c in candles if c.trade_date <= snapshot.as_of]
        assert snapshot == track(plan, past, calendar, snapshot.as_of)
    assert reloaded is not None and reloaded.status is PlanStatus.ACTIVE
    assert reloaded.predicted_pct == plan.predicted_pct


async def test_feature_store_and_labels_round_trip(seeded: UowFactory) -> None:
    built = await BuildFeaturesAndLabels(seeded).execute()
    again = await BuildFeaturesAndLabels(seeded).execute()

    async with seeded() as uow:
        features = await uow.features.load_features(FEATURE_SET_VERSION)
        latest = await uow.features.latest_features(FEATURE_SET_VERSION)
        labels = await uow.features.load_labels(HoldingCategory.D50)
    assert built == again  # idempotent
    assert len(features) == built.features
    assert len(latest) == 50
    assert all(day == max(d for (_, d) in features) for day, _ in latest.values())
    assert labels and all(set(label.hits) == set(TARGET_PCTS) for label in labels.values())


async def test_registry_keeps_one_active_model_and_rolls_back(
    uow_factory: UowFactory, engine: AsyncEngine
) -> None:
    now = datetime(2026, 11, 1, tzinfo=UTC)
    async with uow_factory() as uow:
        first = await uow.models.add(ModelVersion("m1", HoldingCategory.Y1, "lgbm"))
        second = await uow.models.add(ModelVersion("m2", HoldingCategory.Y1, "lgbm"))
        assert first.id and second.id
        await uow.models.activate(first.id, now)
        await uow.models.activate(second.id, now + timedelta(days=7))
        await uow.commit()

    async with uow_factory() as uow:
        assert (active := await uow.models.active(HoldingCategory.Y1)) and active.name == "m2"
        restored = await uow.models.rollback(HoldingCategory.Y1, now + timedelta(days=8))
        await uow.commit()
    assert restored and restored.name == "m1"

    async with engine.begin() as connection:
        with pytest.raises(IntegrityError):  # the database itself forbids two ACTIVE rows
            await connection.execute(
                text("UPDATE model_versions SET status = 'ACTIVE' WHERE category = '1Y'")
            )


async def test_credentials_are_stored_encrypted_and_primary_is_kept(
    uow_factory: UowFactory, engine: AsyncEngine
) -> None:
    async with uow_factory() as uow:
        await uow.stocks.ensure_market("IN", "India", "INR", "Asia/Kolkata")
        await uow.providers.ensure("eodhd", "MARKET_DATA", "EODHD")
        await uow.providers.set_credential("eodhd", "api_token", b"ciphertext", "1a2b")
        await uow.providers.set_credential("eodhd", "api_token", b"ciphertext-2", "9z9z")
        await uow.providers.set_primary("IN", "MARKET_DATA", "eodhd")
        await uow.commit()

    async with uow_factory() as uow:
        assert await uow.providers.credentials("eodhd") == {"api_token": b"ciphertext-2"}
        assert await uow.providers.credential_hints("eodhd") == {"api_token": "9z9z"}
        assert await uow.providers.primary("IN", "MARKET_DATA") == "eodhd"
        await uow.providers.delete_credentials("eodhd")
        await uow.commit()

    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM provider_credentials")) == 0


async def test_nearest_setups_use_pgvector_and_respect_the_cutoff(seeded: UowFactory) -> None:
    await BuildFeaturesAndLabels(seeded).execute()
    async with seeded() as uow:
        latest = await uow.features.latest_features(FEATURE_SET_VERSION)
        as_of, features = next(iter(latest.values()))
        cutoff = as_of - timedelta(days=50)
        found = await uow.features.nearest(
            FEATURE_SET_VERSION, embedding(features), HoldingCategory.D50, cutoff, 10
        )

    assert len(found) == 10
    assert all(a.as_of < cutoff for a in found)
    distances = [a.distance for a in found]
    assert distances == sorted(distances)
    assert all(0 <= d <= 2 for d in distances)


async def test_screener_answers_2000_stocks_in_under_two_seconds(
    uow_factory: UowFactory, engine: AsyncEngine
) -> None:
    stocks, categories = 2000, [c.value for c in HoldingCategory]
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO markets (code, name, currency, timezone) "
                "VALUES ('IN', 'India', 'INR', 'Asia/Kolkata')"
            )
        )
        await connection.execute(
            text(
                "INSERT INTO stocks (market_code, exchange, symbol, name, sector, currency,"
                " timezone, source_provider) SELECT 'IN', 'NSE', 'S' || g, 'Stock ' || g,"
                " 'Sector ' || (g % 12), 'INR', 'Asia/Kolkata', 'mock'"
                " FROM generate_series(1, :n) g"
            ),
            {"n": stocks},
        )
        await connection.execute(
            text(
                "INSERT INTO model_versions (name, algorithm, status)"
                " VALUES ('bench', 'bench', 'CANDIDATE')"
            )
        )
        for days_back in (7, 0):  # two prediction dates: the screener must pick the newest
            await connection.execute(
                text(
                    "INSERT INTO predictions (stock_id, as_of, category, p10_pct, p50_pct,"
                    " p90_pct, prob_up, prob_hit, model_version_id)"
                    " SELECT s.id, DATE '2026-10-30' - CAST(:back AS integer), c,"
                    " -5 - (s.id % 7), (s.id % 11),"
                    " 12 + (s.id % 9), 0.55, jsonb_build_object('5', 0.6, '10', 0.4 + (s.id % 5)"
                    " / 100.0, '15', 0.3, '20', 0.2, '25', 0.15, '30', 0.1, '40', 0.05,"
                    " '50', 0.02),"
                    " (SELECT id FROM model_versions WHERE name = 'bench')"
                    " FROM stocks s CROSS JOIN unnest(CAST(:categories AS text[])) c"
                ),
                {"back": days_back, "categories": categories},
            )
        await connection.execute(text("ANALYZE predictions"))

    started = time.perf_counter()
    rows = await ScreenerQueries(uow_factory).screen(
        ScreenCriteria(HoldingCategory.Y1, target_pct=10, min_probability=Decimal("0.42"))
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0, f"screener took {elapsed:.2f} s"
    assert rows and all(r.prediction.as_of == date(2026, 10, 30) for r in rows)
    assert all((r.probability or 0) >= Decimal("0.42") for r in rows)
