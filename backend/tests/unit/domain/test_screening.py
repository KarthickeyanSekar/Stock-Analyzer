from datetime import date
from decimal import Decimal

from stock_analyzer.domain.analysis.quality import quality_score
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS, Prediction, ReturnRange
from stock_analyzer.domain.prediction.screening import (
    Candidate,
    ScreenCriteria,
    best_category,
    probability_of,
    risk_adjusted,
    screen,
    target_level,
)

D = Decimal


def prediction(
    category: HoldingCategory = HoldingCategory.D50,
    p10: str = "-5",
    p50: str = "8",
    p90: str = "20",
    prob20: str = "0.3",
) -> Prediction:
    probs = {t: D(prob20) * D(20) / D(t) if t >= 20 else D("0.6") for t in TARGET_PCTS}
    return Prediction(
        stock_id=1,
        as_of=date(2026, 10, 30),
        category=category,
        range=ReturnRange(D(p10), D(p50), D(p90)),
        prob_up=D("0.6"),
        prob_hit=probs,
    )


def candidate(symbol: str, sector: str = "IT", quality: int = 6, **kw: str) -> Candidate:
    return Candidate(symbol, sector, prediction(**kw), quality)  # type: ignore[arg-type]


def test_quality_score_bands_and_missing_values() -> None:
    best = {
        "roe_rank": 0.9,
        "revenue_yoy_rank": 0.8,
        "earnings_yield_rank": 0.7,
        "volatility_1y_rank": 0.1,
        "debt_to_equity": 0.2,
    }
    assert quality_score(best) == 10
    assert quality_score({}) == 0
    assert quality_score(best | {"debt_to_equity": 0.8, "roe_rank": 0.5}) == 8


def test_target_level_maps_to_the_next_predicted_target() -> None:
    assert target_level(20) == 20
    assert target_level(18) == 20
    assert target_level(51) is None
    assert probability_of(prediction(prob20="0.3"), 20) == D("0.3")


def test_screen_filters_and_ranks() -> None:
    rows = [
        candidate("AAA", prob20="0.30", p50="8"),
        candidate("BBB", prob20="0.40", p50="5"),
        candidate("CCC", prob20="0.40", p50="9"),
        candidate("DDD", prob20="0.50", p10="-15"),  # too much downside
        candidate("EEE", prob20="0.60", quality=2),  # low quality
        candidate("FFF", prob20="0.60", sector="Banks"),  # other sector
        candidate("GGG", prob20="0.60", category=HoldingCategory.Y1),  # other period
    ]
    criteria = ScreenCriteria(
        HoldingCategory.D50,
        target_pct=20,
        min_probability=D("0.3"),
        min_worst_pct=D(-8),
        min_quality=5,
        sectors=frozenset({"IT"}),
    )

    assert [c.symbol for c in screen(rows, criteria)] == ["CCC", "BBB", "AAA"]
    assert screen(rows, ScreenCriteria(HoldingCategory.D50, target_pct=60)) == []


def test_best_category_is_median_per_unit_of_downside() -> None:
    d50 = prediction(HoldingCategory.D50, p10="-5", p50="5")  # 5 / 10 = 0.5
    y1 = prediction(HoldingCategory.Y1, p10="-10", p50="15")  # 15 / 25 = 0.6
    negative = prediction(HoldingCategory.Y2, p10="-20", p50="-1")

    assert risk_adjusted(negative) is None
    assert best_category([d50, y1, negative]) is HoldingCategory.Y1
    tie = prediction(HoldingCategory.D100, p10="-5", p50="5")
    assert best_category([tie, d50]) is HoldingCategory.D50  # tie → shorter period
    assert best_category([negative]) is None
