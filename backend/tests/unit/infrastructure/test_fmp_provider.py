import logging
from datetime import date
from decimal import Decimal

import pytest

from stock_analyzer.application.errors import ProviderError
from stock_analyzer.infrastructure.logging.setup import configure_logging
from stock_analyzer.infrastructure.providers.fmp.provider import FmpProvider
from tests.fmp_fixtures import VALID_KEY, client

START, END = date(2020, 1, 1), date(2026, 10, 30)


def provider(**responses: list[int]) -> FmpProvider:
    return FmpProvider(VALID_KEY, client=client(responses or None), sleep=lambda _s: None)


def test_daily_candles_join_adjusted_close_and_skip_bad_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    candles = provider().daily_candles("RELIANCE", START, END)

    assert [c.trade_date for c in candles] == [
        date(2026, 10, 27),
        date(2026, 10, 28),
        date(2026, 10, 30),  # the 29th has open > high and is dropped
    ]
    assert candles[1].close == Decimal("2930.0")
    assert candles[1].adj_close == Decimal("2920.0")  # dividend-adjusted
    assert candles[0].adj_close == candles[0].close  # no adjusted row → close
    assert "skipped 1 invalid" in caplog.text


def test_unknown_ticker_returns_no_data() -> None:
    assert provider().daily_candles("NOPE", START, END) == []
    assert provider().quarterly_fundamentals("NOPE", START, END) == []


def test_fundamentals_map_to_crore_and_point_in_time() -> None:
    quarters = provider().quarterly_fundamentals("RELIANCE", START, END)

    # 2025-12-31 has no net income → skipped.
    assert [q.period_end for q in quarters] == [date(2026, 3, 31), date(2026, 6, 30)]
    march, june = quarters
    assert june.revenue_cr == Decimal("240000.00")
    assert june.eps == Decimal("14.05")
    assert march.eps == (Decimal("185000000000") / Decimal("13530000000")).quantize(Decimal("0.01"))
    assert june.announced_date == date(2026, 7, 18)  # the filing date
    assert march.debt_to_equity == (Decimal("3e12") / Decimal("8.3e12")).quantize(Decimal("0.01"))
    assert june.roe_pct == (Decimal("19e10") * 4 / Decimal("8.5e12") * 100).quantize(
        Decimal("0.01")
    )


def test_fundamentals_respect_the_as_of_date() -> None:
    before_june_results = provider().quarterly_fundamentals("RELIANCE", START, date(2026, 7, 10))

    assert [q.period_end for q in before_june_results] == [date(2026, 3, 31)]


def test_retries_on_rate_limit_then_succeeds() -> None:
    p = provider(**{"/stable/historical-price-eod/full": [429, 503]})

    assert len(p.daily_candles("RELIANCE", START, END)) == 3


def test_plan_without_india_gives_a_clear_error() -> None:
    p = provider(**{"/stable/quote": [402]})

    check = p.test_connection()
    assert not check.is_ok and "paid plan" in check.message


def test_bad_key_gives_a_clear_error_without_the_key(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging("DEBUG")
    caplog.set_level(logging.DEBUG)
    secret = "secret-key-9z9z"  # noqa: S105 - fake value used to prove it never leaks
    bad = FmpProvider(secret, client=client(), sleep=lambda _s: None)

    with pytest.raises(ProviderError, match="check it in Admin") as error:
        bad.daily_candles("RELIANCE", START, END)

    assert secret not in str(error.value)
    assert secret not in caplog.text
    check = bad.test_connection()
    assert not check.is_ok and secret not in check.message


def test_connection_fetches_an_nse_quote() -> None:
    check = provider().test_connection()

    assert check.is_ok
    assert check.message == "Connected: NSE data available (RELIANCE 2950.0)"


def test_empty_key_is_refused() -> None:
    with pytest.raises(ProviderError, match="needs an API key"):
        FmpProvider("")
