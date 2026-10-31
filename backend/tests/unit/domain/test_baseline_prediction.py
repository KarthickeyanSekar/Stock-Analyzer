from datetime import date, timedelta
from decimal import Decimal

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.baseline import MODEL_VERSION, empirical_prediction
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS

AS_OF = date(2025, 12, 31)


def rising_closes(days: int, daily_growth: str = "1.001") -> list[tuple[date, Decimal]]:
    """Steadily rising prices, one per calendar day ending on AS_OF."""
    growth, price, closes = Decimal(daily_growth), Decimal("100"), []
    for offset in range(days):
        closes.append((AS_OF - timedelta(days=days - 1 - offset), price))
        price *= growth
    return closes


def test_prediction_has_ordered_range_and_probabilities() -> None:
    prediction = empirical_prediction(
        stock_id=1, as_of=AS_OF, category=HoldingCategory.D50, closes=rising_closes(800)
    )

    assert prediction is not None
    assert prediction.range.p10_pct <= prediction.range.p50_pct <= prediction.range.p90_pct
    assert prediction.prob_up == Decimal("1.0000")  # always rising
    assert set(prediction.prob_hit) == set(TARGET_PCTS)
    assert prediction.model_version == MODEL_VERSION


def test_target_probabilities_never_increase_as_the_target_rises() -> None:
    prediction = empirical_prediction(
        stock_id=1, as_of=AS_OF, category=HoldingCategory.D100, closes=rising_closes(900, "1.002")
    )

    assert prediction is not None
    probs = [prediction.prob_hit[target] for target in TARGET_PCTS]
    assert probs == sorted(probs, reverse=True)


def test_no_future_data_is_used() -> None:
    # Arrange: identical history, plus a huge crash AFTER as_of in the second series
    history = rising_closes(800)
    crash_after = [(AS_OF + timedelta(days=d), Decimal("1")) for d in range(1, 200)]

    # Act
    without_future = empirical_prediction(
        stock_id=1, as_of=AS_OF, category=HoldingCategory.D50, closes=history
    )
    with_future = empirical_prediction(
        stock_id=1, as_of=AS_OF, category=HoldingCategory.D50, closes=history + crash_after
    )

    # Assert: the crash after as_of changes nothing
    assert without_future == with_future


def test_too_little_history_returns_none() -> None:
    assert (
        empirical_prediction(
            stock_id=1, as_of=AS_OF, category=HoldingCategory.Y3, closes=rising_closes(400)
        )
        is None
    )
