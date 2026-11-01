import random
from datetime import date, timedelta

import pytest

from stock_analyzer.domain.prediction import evaluation as ev
from stock_analyzer.domain.prediction.labels import make_label


def test_label_triple_barrier() -> None:
    label = make_label([105.0, 112.0, 95.0, 90.0, 99.0], entry=100.0, horizon=5)

    assert label is not None
    assert label.forward_return_pct == pytest.approx(-1.0)
    assert label.hits[10] and not label.hits[15]
    assert label.is_stopped  # 90 ≤ 93 after the target
    assert label.first_barrier(10) == "TARGET"
    assert label.first_barrier(20) == "STOP"


def test_label_time_barrier_and_missing_future() -> None:
    label = make_label([101.0, 102.0], entry=100.0, horizon=2)
    assert label is not None and label.first_barrier(5) == "TIME"
    assert make_label([101.0], entry=100.0, horizon=2) is None  # horizon passes the data


def test_walk_forward_folds_are_purged() -> None:
    dates = [date(2024, 1, 1) + timedelta(days=7 * i) for i in range(100)]

    folds = ev.walk_forward_folds(dates, n_folds=3, embargo=10, min_train=40)

    assert len(folds) == 3
    for fold in folds:
        gap = [d for d in dates if fold.train_end <= d < fold.test_start]
        assert len(gap) == 10  # embargo dates dropped between train and test
    assert folds[-1].test_end == dates[-1]
    assert ev.walk_forward_folds(dates[:20], 3, 10, 40) == []


def test_scores() -> None:
    assert ev.pinball_loss([1.0, 3.0], [2.0, 2.0], 0.5) == pytest.approx(0.5)
    assert ev.coverage([1, 5, 9], [0, 0, 0], [6, 6, 6]) == pytest.approx(2 / 3)
    assert ev.direction_accuracy([1, -1, 2], [0.5, 0.5, 3]) == pytest.approx(2 / 3)
    perfect = ev.expected_calibration_error([True, False] * 50, [0.5] * 100)
    assert perfect == pytest.approx(0.0)
    assert ev.expected_calibration_error([True] * 10, [0.0] * 10) == pytest.approx(100.0)


def test_conformal_margin_reaches_the_target_coverage() -> None:
    rng = random.Random(1)  # noqa: S311 - test data, not security
    calib = [rng.gauss(0, 1) for _ in range(2000)]
    test = [rng.gauss(0, 1) for _ in range(2000)]
    # A deliberately too-narrow range [-0.1, 0.1] is widened by the margin.
    margin = ev.conformal_margin(calib, [-0.1] * 2000, [0.1] * 2000)

    covered = ev.coverage(test, [-0.1 - margin] * 2000, [0.1 + margin] * 2000)
    assert 0.77 <= covered <= 0.83


def score(
    pinball: float, cov: float = 0.8, ece: float = 2.0, direction: float = 0.55
) -> ev.FoldScore:
    return ev.FoldScore(pinball, cov, ece, direction, samples=100)


def test_gates_pass_and_fail() -> None:
    good = [score(1.0), score(1.0), score(1.0)]
    base: dict[str, list[ev.FoldScore]] = {
        "universe": [score(1.2)] * 3,
        "momentum": [score(1.1)] * 3,
    }

    assert ev.evaluate_gates(good, base).passed
    assert not ev.evaluate_gates([score(1.3)] * 3, base).checks["beats_baselines"]
    assert not ev.evaluate_gates([score(1.0, ece=7)] * 3, base).checks["calibration"]
    assert not ev.evaluate_gates([score(1.0, cov=0.6)] * 3, base).checks["range_coverage"]
    assert not ev.evaluate_gates([score(1.0, direction=0.9)] * 3, base).checks["no_leakage_alarm"]
    unstable = [score(0.5), score(1.15), score(1.15)]
    assert not ev.evaluate_gates(unstable, base).checks["stability"]
    assert not ev.evaluate_gates(good, base, current=[score(0.9)]).checks["not_worse_than_current"]
    empty = ev.evaluate_gates([], base)
    assert not empty.passed and empty.details["reason"]
