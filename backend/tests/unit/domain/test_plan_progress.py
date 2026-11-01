from datetime import date, timedelta
from decimal import Decimal

import pytest

from stock_analyzer.domain.journal.progress import track
from stock_analyzer.domain.journal.settings import (
    InvalidSettingsError,
    JournalSettings,
    suggest_position,
)
from stock_analyzer.domain.journal.trade_plan import EntrySource, PlanOutcome, TradePlan
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar
from stock_analyzer.domain.pricing.candle import Candle

CALENDAR = TradingCalendar()
START = date(2026, 1, 5)  # a Monday


def make_plan(**overrides: object) -> TradePlan:
    values: dict[str, object] = {
        "stock_id": 1,
        "category": HoldingCategory.D50,
        "start_date": START,
        "planned_end_date": START + timedelta(days=14),
        "entry_price": Decimal(100),
        "target_pct": Decimal(10),
        "stop_pct": Decimal(-5),
    } | overrides
    return TradePlan.start(**values)  # type: ignore[arg-type]


def candle(day: date, close: str, high: str | None = None, low: str | None = None) -> Candle:
    price = Decimal(close)
    return Candle(
        trade_date=day,
        open=price,
        high=Decimal(high) if high else price,
        low=Decimal(low) if low else price,
        close=price,
        adj_close=price,
        volume=1000,
    )


def days(n: int) -> list[date]:
    return CALENDAR.trading_days(START, START + timedelta(days=n))


def test_day_n_of_m_return_and_progress() -> None:
    candles = [candle(d, "100") for d in days(5)] + [candle(START + timedelta(days=7), "105")]

    progress = track(make_plan(), candles, CALENDAR, START + timedelta(days=7))

    assert progress is not None
    assert (progress.day_number, progress.total_days) == (5, 10)  # 2 weeks = 10 sessions
    assert progress.return_pct == Decimal("5.0000")
    # stop 95 → 0, target 110 → 100: 105 is two thirds of the way
    assert progress.progress_pct == Decimal("66.6667")
    assert not (progress.is_target_reached or progress.is_stop_hit or progress.is_end_date_reached)


@pytest.mark.parametrize(
    ("high", "low", "target_hit", "stop_hit"),
    [("110", "100", True, False), ("109.95", "100", False, False), ("100", "95", False, True)],
)
def test_target_and_stop_flags_use_the_day_range(
    high: str, low: str, target_hit: bool, stop_hit: bool
) -> None:
    day = START + timedelta(days=1)
    candles = [candle(START, "100"), candle(day, "100", high=high, low=low)]

    progress = track(make_plan(), candles, CALENDAR, day)

    assert progress is not None
    assert progress.is_target_reached is target_hit
    assert progress.is_stop_hit is stop_hit
    assert progress.target_reached_on == (day if target_hit else None)


def test_start_day_range_is_ignored_and_future_candles_are_not_used() -> None:
    plan = make_plan()
    candles = [candle(START, "100", high="120", low="80"), candle(START + timedelta(days=1), "101")]
    future = [*candles, candle(START + timedelta(days=2), "130", high="130")]

    on_day_one = track(plan, future, CALENDAR, START + timedelta(days=1))

    assert on_day_one is not None
    assert on_day_one.last_close == Decimal(101)  # the day-2 candle is never seen
    assert not on_day_one.is_target_reached
    assert not on_day_one.is_stop_hit


def test_end_date_reached_and_day_number_capped() -> None:
    plan = make_plan()
    candles = [candle(d, "100") for d in days(20)]

    progress = track(plan, candles, CALENDAR, START + timedelta(days=20))

    assert progress is not None
    assert progress.is_end_date_reached
    assert progress.day_number == progress.total_days


def test_progress_stops_at_the_planned_end_date() -> None:
    plan = make_plan()
    candles = [candle(d, "100") for d in days(14)] + [
        candle(START + timedelta(days=21), "150", high="150", low="150")
    ]

    progress = track(plan, candles, CALENDAR, START + timedelta(days=21))

    assert progress is not None
    assert progress.as_of == plan.planned_end_date
    assert progress.last_close == Decimal(100)  # the later 150 is outside the plan
    assert not progress.is_target_reached


def test_tracking_never_closes_a_plan() -> None:
    plan = make_plan()
    track(plan, [candle(START + timedelta(days=1), "200", high="200")], CALENDAR, date.max)

    assert plan.outcome is None and plan.exit_price is None


def test_no_progress_without_prices() -> None:
    assert track(make_plan(), [], CALENDAR, START) is None


def test_outcome_judged_against_prediction_when_present() -> None:
    plan = make_plan(predicted_pct=Decimal(6), reference_close=Decimal(100))
    assert plan.entry_source is EntrySource.CLOSE

    assert plan.close(START + timedelta(days=14), Decimal("106.2")) is PlanOutcome.SUCCESS
    assert plan.is_own_target_met is False
    assert plan.own_target_gap_pp == Decimal("-3.8000")


def test_typed_entry_price_is_manual() -> None:
    plan = make_plan(entry_price=Decimal(101), reference_close=Decimal(100))

    assert plan.entry_source is EntrySource.MANUAL
    assert plan.benchmark_pct == Decimal(10)  # no prediction → judged against the target


def test_position_size_risks_the_chosen_share_of_capital() -> None:
    size = suggest_position(Decimal(1000000), Decimal(1), Decimal(-5), Decimal("333.30"))

    assert size.risk_amount == Decimal("10000.00")
    assert size.quantity == 600  # 2,00,000 / 333.30 = 600.06 → whole shares
    assert size.amount == Decimal("199980.00")


def test_position_size_is_capped_at_the_capital() -> None:
    size = suggest_position(Decimal(100000), Decimal(5), Decimal("-0.5"), Decimal(100))

    assert size.amount <= Decimal(100000)


@pytest.mark.parametrize(
    "bad",
    [
        {"paper_capital": Decimal(0)},
        {"risk_pct": Decimal(0)},
        {"risk_pct": Decimal(11)},
        {"success_tolerance_pp": Decimal(-1)},
        {"default_stop_pct": Decimal(1)},
    ],
)
def test_settings_validation(bad: dict[str, Decimal]) -> None:
    with pytest.raises(InvalidSettingsError):
        JournalSettings(**bad)
