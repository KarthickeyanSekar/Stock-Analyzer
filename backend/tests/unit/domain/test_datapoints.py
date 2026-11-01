import math
from datetime import date, timedelta
from decimal import Decimal

import pytest

from stock_analyzer.domain.analysis import datapoints as dp
from stock_analyzer.domain.analysis.features import (
    ALL_FEATURES,
    AdjustedSeries,
    add_ranks,
    build_features,
)
from stock_analyzer.domain.fundamentals.quarterly_fundamentals import QuarterlyFundamentals
from stock_analyzer.domain.pricing.candle import Candle


def test_moving_average_and_distance() -> None:
    closes = [float(x) for x in range(1, 201)]  # 1 … 200

    assert dp.sma(closes, 50) == pytest.approx(175.5)
    assert dp.price_vs_ma(closes, 50) == pytest.approx(200 / 175.5 - 1)
    assert dp.golden_cross(closes) == 1.0  # rising: fast MA above slow MA
    assert dp.sma(closes, 201) is None
    assert dp.distance_from_high(closes, 200) == 0.0
    assert dp.distance_from_low(closes, 200) == pytest.approx(199.0)


def test_momentum_skips_the_recent_month() -> None:
    closes = [100.0] * 200 + [110.0] * 50 + [200.0]  # last day jumps

    assert dp.momentum(closes, 21) == pytest.approx(200 / 110 - 1)  # 110 → 200
    assert dp.momentum(closes, 250, skip=21) == pytest.approx(0.1)  # ignores the jump
    assert dp.momentum(closes[:10], 21) is None


def test_volatility_drawdown_beta() -> None:
    closes = [100.0 * (1.01 if i % 2 else 0.99) ** 0 for i in range(10)]
    assert dp.volatility([100.0] * 300) == 0.0
    assert dp.max_drawdown([100, 120, 90, 110], 4) == pytest.approx(90 / 120 - 1)
    market = [0.01, -0.02, 0.015, -0.005] * 70
    assert dp.beta([2 * r for r in market], market) == pytest.approx(2.0)
    assert dp.volatility(closes) is None


def test_atr_and_volume_trend() -> None:
    highs, lows, closes = [11.0] * 20, [9.0] * 20, [10.0] * 20
    assert dp.atr_pct(highs, lows, closes) == pytest.approx(0.2)
    assert dp.volume_trend([100.0] * 80 + [200.0] * 20) == pytest.approx(200 / 120)


def test_valuation_and_growth() -> None:
    assert dp.pe_ratio(100, 5) == 20
    assert dp.pe_ratio(100, -1) is None  # P/E undefined for losses
    assert dp.earnings_yield(100, -1) == -0.01
    assert dp.pb_ratio(100, 50) == 2
    assert dp.peg_ratio(20, 0.10) == 2
    assert dp.graham_number(4, 25) == pytest.approx(math.sqrt(2250))
    assert dp.growth(110, 100) == pytest.approx(0.1)
    assert dp.cagr(133.1, 100, 3) == pytest.approx(0.1)
    assert dp.cagr(100, 0, 3) is None


def test_percentile_ranks_handle_ties_and_missing() -> None:
    ranks = dp.percentile_ranks({1: 10.0, 2: 20.0, 3: 20.0, 4: None, 5: 30.0})
    assert ranks == {1: 0.0, 2: 0.5, 3: 0.5, 4: None, 5: 1.0}


def candles(n: int, start: date = date(2024, 1, 1)) -> list[Candle]:
    out, day = [], start
    for i in range(n):
        price = Decimal(100 + i % 7)
        out.append(Candle(day, price, price + 1, price - 1, price, price, 1000 + i))
        day += timedelta(days=1)
    return out


def quarter(end: date, eps: str = "5") -> QuarterlyFundamentals:
    return QuarterlyFundamentals(
        period_end=end,
        announced_date=end + timedelta(days=40),
        revenue_cr=Decimal(1000),
        net_profit_cr=Decimal(100),
        eps=Decimal(eps),
        book_value_per_share=Decimal(50),
        roe_pct=Decimal(15),
        debt_to_equity=Decimal("0.5"),
    )


def test_features_complete_with_enough_history() -> None:
    series = AdjustedSeries.from_candles(candles(300))
    as_of = series.days[-1]
    quarters = [quarter(date(2023, 3 * m, 28)) for m in range(1, 5)]
    market = dict.fromkeys(series.days, 0.0)

    features = build_features(as_of, series, market, quarters)

    assert features["pe"] == pytest.approx(float(series.last_raw_close) / 20)
    assert features["roe"] == pytest.approx(0.15)
    assert features["price_vs_200dma"] is not None
    assert features["revenue_yoy"] is None  # needs 5 quarters


def test_features_refuse_future_inputs() -> None:
    series = AdjustedSeries.from_candles(candles(10))
    with pytest.raises(ValueError, match="candles after"):
        build_features(series.days[-2], series, {}, [])
    late = quarter(series.days[-1])  # announced 40 days later
    with pytest.raises(ValueError, match="fundamentals announced after"):
        build_features(series.days[-1], series, {}, [late])


def test_ranks_cover_every_feature_name() -> None:
    series = AdjustedSeries.from_candles(candles(300))
    features = build_features(series.days[-1], series, {}, [])
    ranked = add_ranks({1: features, 2: features})

    assert set(ranked[1]) == set(ALL_FEATURES)
