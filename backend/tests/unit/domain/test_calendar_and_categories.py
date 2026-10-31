from datetime import date

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.market.trading_calendar import TradingCalendar

REPUBLIC_DAY = date(2026, 1, 26)  # Monday


def test_weekends_and_holidays_are_not_trading_days() -> None:
    calendar = TradingCalendar(holidays=[REPUBLIC_DAY])

    assert calendar.is_trading_day(date(2026, 1, 23))  # Friday
    assert not calendar.is_trading_day(date(2026, 1, 24))  # Saturday
    assert not calendar.is_trading_day(REPUBLIC_DAY)
    assert calendar.next_trading_day(date(2026, 1, 24)) == date(2026, 1, 27)


def test_trading_days_lists_only_open_days() -> None:
    calendar = TradingCalendar(holidays=[REPUBLIC_DAY])

    days = calendar.trading_days(date(2026, 1, 23), date(2026, 1, 28))

    assert days == [date(2026, 1, 23), date(2026, 1, 27), date(2026, 1, 28)]


def test_planned_end_date_adds_calendar_days_and_rolls_to_a_trading_day() -> None:
    calendar = TradingCalendar()

    # 2026-01-05 + 50 days = 2026-02-24 (Tuesday)
    assert calendar.planned_end_date(date(2026, 1, 5), HoldingCategory.D50) == date(2026, 2, 24)
    # 2026-01-03 + 365 days = 2027-01-03 (Sunday) → Monday
    assert calendar.planned_end_date(date(2026, 1, 3), HoldingCategory.Y1) == date(2027, 1, 4)


def test_categories_cover_the_planned_horizons() -> None:
    assert [c.value for c in HoldingCategory] == ["50D", "100D", "200D", "300D", "1Y", "2Y", "3Y"]
    assert HoldingCategory.D50.approx_trading_days == 34
    assert HoldingCategory.Y1.approx_trading_days == 250


def test_cagr_is_shown_only_for_one_year_and_longer() -> None:
    shown = {c for c in HoldingCategory if c.shows_cagr}
    assert shown == {HoldingCategory.Y1, HoldingCategory.Y2, HoldingCategory.Y3}
