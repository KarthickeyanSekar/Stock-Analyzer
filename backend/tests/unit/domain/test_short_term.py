from datetime import date
from decimal import Decimal

import pytest

from stock_analyzer.domain.analysis import datapoints as dp
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import Prediction, ReturnRange
from stock_analyzer.domain.prediction.setup import Setup, setup_of


def test_rsi_extremes_and_middle() -> None:
    rising = [100.0 + i for i in range(30)]
    falling = [100.0 - i for i in range(30)]
    flat_up_down = [100.0, 101.0] * 15

    assert dp.rsi(rising) == 100.0
    assert dp.rsi(falling) == pytest.approx(0.0)
    assert dp.rsi(flat_up_down) == pytest.approx(50.0, abs=5)
    assert dp.rsi(rising[:10]) is None


def test_ema_macd_and_gap_follow_the_trend() -> None:
    rising = [100.0 * 1.01**i for i in range(60)]

    assert dp.ema([1.0, 1.0, 1.0], 3) == [1.0, 1.0, 1.0]
    assert dp.ema_gap(rising) is not None and dp.ema_gap(rising) > 0  # type: ignore[operator]
    assert dp.macd_histogram_pct(rising) is not None
    assert dp.macd_histogram_pct(rising[:20]) is None


def test_bollinger_obv_volume() -> None:
    closes = [100.0] * 19 + [110.0]
    pct_b = dp.bollinger_pct_b(closes)
    assert pct_b is not None and pct_b > 1  # a jump closes above the upper band
    assert dp.bollinger_pct_b([100.0] * 20) == 0.5
    ups = [100.0 + i for i in range(25)]
    assert dp.obv_trend(ups, [10.0] * 25) == pytest.approx(1.0)
    assert dp.volume_spike([10.0] * 20 + [30.0]) == pytest.approx(3.0)


def prediction(prob_up: str, median: str) -> Prediction:
    return Prediction(
        stock_id=1,
        as_of=date(2026, 10, 30),
        category=HoldingCategory.S5,
        range=ReturnRange(Decimal(-3), Decimal(median), Decimal(5)),
        prob_up=Decimal(prob_up),
    )


@pytest.mark.parametrize(
    ("prob_up", "median", "expected"),
    [
        ("0.60", "1.0", Setup.FAVOURABLE),
        ("0.60", "0.2", Setup.NEUTRAL),  # median doesn't cover costs
        ("0.50", "0.5", Setup.NEUTRAL),
        ("0.45", "0.5", Setup.UNFAVOURABLE),
        ("0.60", "-0.1", Setup.UNFAVOURABLE),
    ],
)
def test_setup_label(prob_up: str, median: str, expected: Setup) -> None:
    assert setup_of(prediction(prob_up, median)) is expected
