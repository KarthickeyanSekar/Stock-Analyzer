from datetime import date

import pytest

from stock_analyzer.application.use_cases.validation.run_validation import (
    CategoryValidation,
    verdict,
)
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.validation.backtest import (
    CostModel,
    ExitReason,
    Trade,
    simulate,
    summarise,
)
from stock_analyzer.domain.validation.reliability import reliability


@pytest.mark.parametrize(
    ("closes", "expected"),
    [
        ([101.0, 106.0, 90.0], (6.0, 2, ExitReason.TARGET)),
        ([99.0, 92.0, 120.0], (-8.0, 2, ExitReason.STOP)),
        ([101.0, 102.0, 103.0], (3.0, 3, ExitReason.TIME)),
    ],
)
def test_simulate_exits_at_the_first_barrier(
    closes: list[float], expected: tuple[float, int, ExitReason]
) -> None:
    result = simulate(closes, entry=100.0, target_pct=5, stop_pct=-7, horizon=3)

    assert result is not None
    assert result[0] == pytest.approx(expected[0])
    assert result[1:] == expected[1:]
    assert simulate([101.0], entry=100.0, target_pct=5, stop_pct=-7, horizon=3) is None


def test_costs_and_tax_are_conservative() -> None:
    costs = CostModel()

    assert costs.net(10.0, 100) == pytest.approx((10 - 0.25) * 0.80)  # STCG 20%
    assert costs.net(10.0, 400) == pytest.approx((10 - 0.25) * 0.875)  # LTCG 12.5%
    assert costs.net(-5.0, 100) == pytest.approx(-5.25)  # no tax credit on a loss
    assert costs.net(0.1, 100) == pytest.approx(-0.15)  # costs can turn a gain into a loss


def trade(net: float, benchmark: float, reason: ExitReason = ExitReason.TIME) -> Trade:
    return Trade("X", "50D", date(2025, 1, 1), net, net, 20, reason, benchmark, 0.4)


def test_summary_metrics() -> None:
    summary = summarise(
        [trade(10, 2, ExitReason.TARGET), trade(-5, 2, ExitReason.STOP), trade(4, 2)]
    )

    assert summary is not None
    assert summary.win_rate == pytest.approx(2 / 3)
    assert summary.avg_gain_pct == pytest.approx(7)
    assert summary.avg_loss_pct == pytest.approx(-5)
    assert summary.expectancy_pct == pytest.approx(3)
    assert summary.beats_benchmark
    assert summary.target_hit_rate == pytest.approx(1 / 3)
    assert summarise([]) is None


def test_reliability_buckets() -> None:
    rows = reliability([True, False, True, True], [0.05, 0.08, 0.42, 0.45])

    assert [(r.low, r.count) for r in rows] == [(0.0, 2), (0.4, 2)]
    assert rows[0].observed == pytest.approx(0.5)
    assert rows[1].mean_predicted == pytest.approx(0.435)


def good() -> CategoryValidation:
    v = CategoryValidation(HoldingCategory.D50, 5)
    v.summary = summarise([trade(5, 1)])
    v.ece_pp, v.coverage, v.journal_closed = 3.0, 0.8, 40
    v.journal_outcomes = {"SUCCESS": 20, "PARTIAL": 5, "FAILURE": 15}
    return v


def test_verdict_rules() -> None:
    assert verdict(good(), is_synthetic=False) == ("go", [])
    assert verdict(good(), is_synthetic=True)[0] == "not decidable"
    thin = good()
    thin.journal_closed = 10
    assert verdict(thin, is_synthetic=False) == (
        "no-go",
        ["fewer than 30 closed journal plans"],
    )
    loose = good()
    loose.coverage = 0.6
    assert "80% range coverage outside 75-85%" in verdict(loose, is_synthetic=False)[1]
