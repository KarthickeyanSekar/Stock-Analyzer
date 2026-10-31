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
