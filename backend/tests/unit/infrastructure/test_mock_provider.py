from datetime import date
from decimal import Decimal

import pytest

from stock_analyzer.infrastructure.providers.mock.provider import (
    DEFAULT_END,
    DEFAULT_START,
    MockMarketDataProvider,
)
from stock_analyzer.infrastructure.providers.mock.universe import SAMPLE_HOLIDAYS


@pytest.fixture(scope="module")
def provider() -> MockMarketDataProvider:
    return MockMarketDataProvider()


def test_universe_is_50_nse_stocks_labelled_mock(provider: MockMarketDataProvider) -> None:
    stocks = provider.list_instruments()

    assert len(stocks) == 50
    assert len({stock.symbol for stock in stocks}) == 50
    assert {(s.market_code, s.exchange, s.currency, s.source_provider) for s in stocks} == {
        ("IN", "NSE", "INR", "mock")
    }


def test_five_years_of_trading_days_without_weekends_or_holidays(
    provider: MockMarketDataProvider,
) -> None:
    candles = provider.daily_candles("INFY", DEFAULT_START, DEFAULT_END)
    days = [candle.trade_date for candle in candles]

    # ~257 per year: the sample calendar has 5 fixed holidays (real NSE ~15, ~250 days)
    assert 1200 < len(days) < 1300
    assert all(day.weekday() < 5 for day in days)
    assert not set(days) & SAMPLE_HOLIDAYS
    assert days == sorted(days)


def test_prices_use_the_nse_tick_size(provider: MockMarketDataProvider) -> None:
    for candle in provider.daily_candles("TCS", DEFAULT_START, DEFAULT_END)[:200]:
        assert candle.close % Decimal("0.05") == 0


def test_same_seed_gives_identical_data_and_another_seed_differs() -> None:
    first = MockMarketDataProvider(seed=7).daily_candles("SBIN", DEFAULT_START, DEFAULT_END)
    second = MockMarketDataProvider(seed=7).daily_candles("SBIN", DEFAULT_START, DEFAULT_END)
    other = MockMarketDataProvider(seed=8).daily_candles("SBIN", DEFAULT_START, DEFAULT_END)

    assert first == second
    assert first != other


def test_split_raw_prices_before_ex_date_are_ratio_times_adjusted(
    provider: MockMarketDataProvider,
) -> None:
    candles = {c.trade_date: c for c in provider.daily_candles("TITAN", DEFAULT_START, DEFAULT_END)}
    before = candles[date(2024, 3, 8)]  # Friday before the 1:5 split on 2024-03-11
    after = candles[date(2024, 3, 11)]

    assert before.close / before.adj_close == pytest.approx(5, rel=0.001)
    assert after.close == after.adj_close


def test_date_range_filter(provider: MockMarketDataProvider) -> None:
    candles = provider.daily_candles("ITC", date(2026, 1, 1), date(2026, 1, 31))

    assert candles
    assert all(date(2026, 1, 1) <= c.trade_date <= date(2026, 1, 31) for c in candles)


def test_quarters_are_point_in_time_and_repeatable(provider: MockMarketDataProvider) -> None:
    quarters = provider.quarterly_fundamentals("INFY", DEFAULT_START, DEFAULT_END)

    # Nov 2021 .. Sep 2026: 20 quarter ends; the Sep 2026 quarter may still be unannounced
    assert 19 <= len(quarters) <= 20
    assert all(q.period_end < q.announced_date <= DEFAULT_END for q in quarters)
    assert [q.period_end for q in quarters] == sorted(q.period_end for q in quarters)
    assert quarters == list(
        MockMarketDataProvider().quarterly_fundamentals("INFY", DEFAULT_START, DEFAULT_END)
    )


def test_quarters_announced_after_the_window_are_hidden(provider: MockMarketDataProvider) -> None:
    end = date(2024, 4, 15)  # Q4 FY24 (31 Mar) results are not out yet on 15 Apr
    quarters = provider.quarterly_fundamentals("TCS", DEFAULT_START, end)

    assert quarters
    assert all(q.announced_date <= end for q in quarters)
    assert date(2024, 3, 31) not in {q.period_end for q in quarters}


def test_fundamentals_are_plausible(provider: MockMarketDataProvider) -> None:
    for quarter in provider.quarterly_fundamentals("RELIANCE", DEFAULT_START, DEFAULT_END):
        assert quarter.revenue_cr > quarter.net_profit_cr > 0
        assert quarter.eps > 0
        assert quarter.book_value_per_share > 0
        assert Decimal(0) < quarter.roe_pct < Decimal(100)
