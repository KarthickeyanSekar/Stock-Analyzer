from datetime import date
from decimal import Decimal

import pytest

from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals


def make_quarter(announced: date, book_value: str = "120") -> QuarterlyFundamentals:
    return QuarterlyFundamentals(
        period_end=date(2026, 6, 30),
        announced_date=announced,
        revenue_cr=Decimal("1000"),
        net_profit_cr=Decimal("120"),
        eps=Decimal("12"),
        book_value_per_share=Decimal(book_value),
        roe_pct=Decimal("16"),
        debt_to_equity=Decimal("0.4"),
    )


def test_known_only_from_the_announcement_date() -> None:
    quarter = make_quarter(date(2026, 7, 20))

    assert not quarter.is_known_on(date(2026, 7, 19))
    assert quarter.is_known_on(date(2026, 7, 20))


def test_cannot_be_announced_before_the_quarter_ends() -> None:
    with pytest.raises(ValueError, match="announced before"):
        make_quarter(date(2026, 6, 30))


def test_rejects_impossible_figures() -> None:
    with pytest.raises(ValueError, match="impossible"):
        make_quarter(date(2026, 7, 20), book_value="0")
