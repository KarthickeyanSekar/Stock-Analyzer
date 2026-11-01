from decimal import Decimal

import pytest

from stock_analyzer.domain.shared.money import Money, Percentage

INR = "INR"


def test_money_is_exact_and_immutable() -> None:
    total = Money(Decimal("0.10"), INR) + Money(Decimal("0.20"), INR)

    assert total == Money(Decimal("0.30"), INR)  # no float rounding error
    with pytest.raises(AttributeError):
        total.amount = Decimal(1)  # type: ignore[misc]


@pytest.mark.parametrize("bad", [0.1, 1, True, Decimal("NaN"), Decimal("Infinity")])
def test_money_rejects_non_decimal_and_non_finite(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Money(bad, INR)  # type: ignore[arg-type]


def test_money_rejects_mixed_currencies_and_bad_codes() -> None:
    with pytest.raises(ValueError, match="cannot combine"):
        Money(Decimal(1), INR) + Money(Decimal(1), "USD")
    with pytest.raises(ValueError, match="currency"):
        Money(Decimal(1), "inr")


def test_percentage_moves_and_changes_round_trip() -> None:
    entry = Money(Decimal("2950.00"), INR)
    target = entry.apply(Percentage.of("10.49")).rounded()

    assert target == Money(Decimal("3259.46"), INR)
    assert entry.change_to(target) == Percentage(Decimal("10.4902"))
    assert Percentage.of("10.7") - Percentage.of("10.49") == Decimal("0.21")


def test_times_and_ordering() -> None:
    assert Money(Decimal("12.5"), INR).times(Decimal(4)) == Money(Decimal("50.0"), INR)
    assert Percentage.of("5") < Percentage.of("20")
    with pytest.raises(TypeError):
        Percentage(5.0)  # type: ignore[arg-type]
