import logging
from datetime import date
from decimal import Decimal

import pytest
from cryptography.fernet import Fernet

from stock_analyzer.application.errors import ConfigurationError, ProviderError
from stock_analyzer.infrastructure.logging.setup import configure_logging
from stock_analyzer.infrastructure.providers.eodhd.provider import EodhdProvider
from stock_analyzer.infrastructure.security.fernet_cipher import FernetCipher
from tests.eodhd_fixtures import VALID_TOKEN, client

START, END = date(2020, 1, 1), date(2026, 10, 30)


def provider(**responses: list[int]) -> EodhdProvider:
    waits: list[float] = []
    return EodhdProvider(VALID_TOKEN, client=client(responses or None), sleep=waits.append)


def test_daily_candles_parse_and_skip_inconsistent_rows(caplog: pytest.LogCaptureFixture) -> None:
    candles = provider().daily_candles("RELIANCE", START, END)

    assert [c.trade_date for c in candles] == [
        date(2026, 10, 27),
        date(2026, 10, 28),
        date(2026, 10, 30),  # the 29th has open > high and is dropped
    ]
    assert candles[-1].close == Decimal("2950.0")
    assert candles[-1].adj_close == Decimal("2950.0")
    assert "skipped 1 invalid" in caplog.text


def test_unknown_ticker_returns_no_data() -> None:
    assert provider().daily_candles("NOPE", START, END) == []
    assert provider().quarterly_fundamentals("NOPE", START, END) == []


def test_fundamentals_map_to_crore_and_point_in_time() -> None:
    quarters = provider().quarterly_fundamentals("RELIANCE", START, END)

    # 2025-12-31 has no net income → skipped; two usable quarters remain.
    assert [q.period_end for q in quarters] == [date(2026, 3, 31), date(2026, 6, 30)]
    march, june = quarters
    assert june.revenue_cr == Decimal("240000.00")  # ₹2.4 lakh crore
    assert june.eps == Decimal("14.05")  # reported EPS
    assert march.eps == (Decimal("185000000000") / Decimal("13530000000")).quantize(Decimal("0.01"))
    assert june.announced_date == date(2026, 7, 18)  # the earnings report date
    assert march.announced_date == date(2026, 4, 25)
    assert march.debt_to_equity == (Decimal("3e12") / Decimal("8.3e12")).quantize(Decimal("0.01"))
    assert june.roe_pct == (Decimal("19e10") * 4 / Decimal("8.5e12") * 100).quantize(
        Decimal("0.01")
    )


def test_fundamentals_respect_the_as_of_date() -> None:
    before_june_results = provider().quarterly_fundamentals("RELIANCE", START, date(2026, 7, 10))

    assert [q.period_end for q in before_june_results] == [date(2026, 3, 31)]


def test_retries_on_rate_limit_then_succeeds() -> None:
    p = provider(**{"/api/eod/RELIANCE.NSE": [429, 503]})

    assert len(p.daily_candles("RELIANCE", START, END)) == 3


def test_bad_key_gives_a_clear_error_without_the_token(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging("DEBUG")
    caplog.set_level(logging.DEBUG)
    secret = "secret-token-9z9z"  # noqa: S105 - fake value used to prove it never leaks
    bad = EodhdProvider(secret, client=client(), sleep=lambda _s: None)

    with pytest.raises(ProviderError, match="check it in Admin") as error:
        bad.daily_candles("RELIANCE", START, END)

    assert secret not in str(error.value)
    assert secret not in caplog.text
    check = bad.test_connection()
    assert not check.is_ok and secret not in check.message


def test_connection_reports_the_quota() -> None:
    check = provider().test_connection()

    assert check.is_ok
    assert check.message == "Connected (monthly): 120 of 100000 API calls used today"


def test_empty_token_is_refused() -> None:
    with pytest.raises(ProviderError, match="needs an API token"):
        EodhdProvider("")


def test_fernet_round_trip_and_wrong_key() -> None:
    cipher = FernetCipher(Fernet.generate_key().decode())
    token = cipher.encrypt("abc-123")

    assert cipher.decrypt(token) == "abc-123"
    assert b"abc-123" not in token
    with pytest.raises(ConfigurationError, match="SA_MASTER_KEY changed"):
        FernetCipher(Fernet.generate_key().decode()).decrypt(token)
    unset = FernetCipher("")
    assert not unset.is_configured
    with pytest.raises(ConfigurationError, match="not set"):
        unset.encrypt("x")
