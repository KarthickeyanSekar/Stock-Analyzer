"""Model evaluation maths: purged walk-forward folds, scores, conformal ranges and gates.

Pure Python (docs/26-ml-pipeline.md §5). Statistical values are floats (Q64).
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

QUANTILES: tuple[float, float, float] = (0.1, 0.5, 0.9)
RANGE_LEVEL = 0.8  # p10…p90
ECE_BINS = 10

# Quality gates (Q51)
MAX_ECE_PP = 5.0
COVERAGE_MIN, COVERAGE_MAX = 0.75, 0.85
MAX_WORSE_WINDOW_SHARE = 0.30
LEAKAGE_DIRECTION_ACCURACY = 0.70


@dataclass(frozen=True, slots=True)
class Fold:
    """One walk-forward split by date: train strictly before ``train_end``, test in a block."""

    train_end: date  # exclusive
    test_start: date  # inclusive
    test_end: date  # inclusive


def walk_forward_folds(
    dates: Sequence[date], n_folds: int, embargo: int, min_train: int
) -> list[Fold]:
    """Expanding-window folds over the later part of ``dates`` with a purge/embargo gap.

    The last ``embargo`` sample dates before each test block are dropped from training, so no
    training label (which looks ``embargo`` dates ahead) overlaps the test period.

    Args:
        dates: Distinct sample dates (any order).
        n_folds: Number of test blocks.
        embargo: Gap in sample dates (≥ the holding period expressed in sample dates).
        min_train: Minimum training dates for a fold to be used.
    """
    ordered = sorted(set(dates))
    folds: list[Fold] = []
    if n_folds <= 0 or len(ordered) < min_train + embargo + n_folds:
        return folds
    first_test = min_train + embargo
    block = (len(ordered) - first_test) // n_folds
    if block <= 0:
        return folds
    for k in range(n_folds):
        start = first_test + k * block
        end = len(ordered) - 1 if k == n_folds - 1 else start + block - 1
        folds.append(
            Fold(
                train_end=ordered[start - embargo],
                test_start=ordered[start],
                test_end=ordered[end],
            )
        )
    return folds


def pinball_loss(actual: Sequence[float], predicted: Sequence[float], q: float) -> float:
    """Average quantile (pinball) loss; lower is better."""
    total = 0.0
    for y, p in zip(actual, predicted, strict=True):
        diff = y - p
        total += max(q * diff, (q - 1) * diff)
    return total / len(actual)


def mean_pinball(actual: Sequence[float], quantiles: Sequence[Sequence[float]]) -> float:
    """Pinball loss averaged over p10, p50 and p90 predictions (``quantiles[i]`` per level)."""
    return sum(
        pinball_loss(actual, preds, q) for q, preds in zip(QUANTILES, quantiles, strict=True)
    ) / len(QUANTILES)


def coverage(actual: Sequence[float], low: Sequence[float], high: Sequence[float]) -> float:
    """Share of outcomes inside [low, high]."""
    inside = sum(lo <= y <= hi for y, lo, hi in zip(actual, low, high, strict=True))
    return inside / len(actual)


def expected_calibration_error(outcomes: Sequence[bool], probs: Sequence[float]) -> float:
    """ECE in percentage points: weighted |mean prob - hit rate| over equal-width bins."""
    bins: list[list[tuple[bool, float]]] = [[] for _ in range(ECE_BINS)]
    for hit, prob in zip(outcomes, probs, strict=True):
        bins[min(int(prob * ECE_BINS), ECE_BINS - 1)].append((hit, prob))
    total = len(outcomes)
    error = 0.0
    for members in bins:
        if members:
            rate = sum(h for h, _ in members) / len(members)
            mean_prob = sum(p for _, p in members) / len(members)
            error += len(members) / total * abs(mean_prob - rate)
    return error * 100


def direction_accuracy(actual: Sequence[float], median: Sequence[float]) -> float:
    """Share of samples where the predicted median has the sign of the outcome."""
    right = sum((y > 0) == (m > 0) for y, m in zip(actual, median, strict=True))
    return right / len(actual)


def conformal_margin(
    actual: Sequence[float], low: Sequence[float], high: Sequence[float], level: float = RANGE_LEVEL
) -> float:
    """Conformalized quantile regression: the margin that widens [low, high] to ``level``.

    Scores ``max(low - y, y - high)`` on a calibration set; the margin is their
    ``ceil((n + 1) · level) / n`` empirical quantile (may be negative, which narrows the range).
    """
    scores = sorted(max(lo - y, y - hi) for y, lo, hi in zip(actual, low, high, strict=True))
    n = len(scores)
    index = min(n - 1, max(0, math.ceil((n + 1) * level) - 1))
    return scores[index]


@dataclass(frozen=True, slots=True)
class FoldScore:
    """Scores of one model on one test fold."""

    pinball: float
    coverage: float
    ece_pp: float
    direction_accuracy: float
    samples: int


@dataclass(slots=True)
class GateReport:
    """Result of every quality gate; ``passed`` only when all of them pass."""

    checks: dict[str, bool] = field(default_factory=dict)
    details: dict[str, float | str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Whether the candidate may become ACTIVE."""
        return bool(self.checks) and all(self.checks.values())


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def evaluate_gates(
    candidate: Sequence[FoldScore],
    baselines: Mapping[str, Sequence[FoldScore]],
    current: Sequence[FoldScore] | None = None,
) -> GateReport:
    """Apply the Q51 gates to a candidate's walk-forward scores."""
    report = GateReport()
    if not candidate:
        report.checks["enough_data"] = False
        report.details["reason"] = "no walk-forward fold had enough data"
        return report
    report.checks["enough_data"] = True
    pinball = _mean([f.pinball for f in candidate])
    report.details["pinball"] = round(pinball, 4)
    beats_all = True
    worse_windows = 0
    for name, scores in baselines.items():
        base = _mean([f.pinball for f in scores])
        report.details[f"pinball_{name}"] = round(base, 4)
        beats_all = beats_all and pinball < base
    best_baseline_per_fold = [
        min(scores[i].pinball for scores in baselines.values()) for i in range(len(candidate))
    ]
    worse_windows = sum(
        f.pinball > base for f, base in zip(candidate, best_baseline_per_fold, strict=True)
    )
    ece = _mean([f.ece_pp for f in candidate])
    cov = _mean([f.coverage for f in candidate])
    direction = _mean([f.direction_accuracy for f in candidate])
    worse_share = worse_windows / len(candidate)
    report.details |= {
        "ece_pp": round(ece, 2),
        "coverage": round(cov, 4),
        "direction_accuracy": round(direction, 4),
        "worse_window_share": round(worse_share, 4),
    }
    report.checks |= {
        "beats_baselines": beats_all,
        "calibration": ece <= MAX_ECE_PP,
        "range_coverage": COVERAGE_MIN <= cov <= COVERAGE_MAX,
        "stability": worse_share <= MAX_WORSE_WINDOW_SHARE,
        "no_leakage_alarm": direction <= LEAKAGE_DIRECTION_ACCURACY,
    }
    if current:
        report.details["pinball_current"] = round(current[-1].pinball, 4)
        report.checks["not_worse_than_current"] = candidate[-1].pinball <= current[-1].pinball
    return report
