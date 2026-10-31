"""Empirical baseline prediction: what happened after every comparable past start date.

Pure statistics, no ML. For a holding period of ``h`` trading days it collects the forward
return of every historical window that **ended on or before ``as_of``** (so no future data
is used), then reports the p10/p50/p90 returns, the share of windows that ended up, and the
share that reached each target before hitting the stop-loss. It is also the baseline that
the later ML models must beat (docs/26-ml-pipeline.md).
"""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS, Prediction, ReturnRange
from stock_analyzer.domain.shared.percent import round_pct

MODEL_VERSION = "baseline-empirical-v1"
MIN_SAMPLES = 20
DEFAULT_STOP_PCT = -7.0
DEFAULT_STEP = 5  # sample every 5th start date: enough windows, far less work
PROB_PLACES = Decimal("0.0001")


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolation quantile of an already sorted sequence."""
    position = q * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _to_prob(share: float) -> Decimal:
    return Decimal(str(share)).quantize(PROB_PLACES)


def empirical_prediction(  # noqa: PLR0913 - inputs of a statistical estimate
    *,
    stock_id: int,
    as_of: date,
    category: HoldingCategory,
    closes: Sequence[tuple[date, Decimal]],
    stop_pct: float = DEFAULT_STOP_PCT,
    step: int = DEFAULT_STEP,
) -> Prediction | None:
    """Return the baseline prediction, or ``None`` when there are too few past windows.

    Args:
        stock_id: Stock the prediction is for.
        as_of: Prediction date; closes after this date are ignored (no look-ahead).
        category: Holding category; its approximate trading days define the window.
        closes: ``(trade_date, adjusted close)`` pairs in any order.
        stop_pct: Stop-loss in percent points (negative), used for target probabilities.
        step: Use every ``step``-th start date.
    """
    history = [float(price) for day, price in sorted(closes) if day <= as_of]
    horizon = category.approx_trading_days
    stop_ratio = 1 + stop_pct / 100
    returns: list[float] = []
    hits = dict.fromkeys(TARGET_PCTS, 0)

    for start in range(0, len(history) - horizon, step):
        entry = history[start]
        best = 1.0
        for price in history[start + 1 : start + horizon + 1]:
            ratio = price / entry
            if ratio <= stop_ratio:
                break
            best = max(best, ratio)
        returns.append((history[start + horizon] / entry - 1) * 100)
        for target in TARGET_PCTS:
            if best >= 1 + target / 100:
                hits[target] += 1

    if len(returns) < MIN_SAMPLES:
        return None
    ordered = sorted(returns)
    samples = len(ordered)
    return Prediction(
        stock_id=stock_id,
        as_of=as_of,
        category=category,
        range=ReturnRange(
            p10_pct=round_pct(Decimal(str(_quantile(ordered, 0.10)))),
            p50_pct=round_pct(Decimal(str(_quantile(ordered, 0.50)))),
            p90_pct=round_pct(Decimal(str(_quantile(ordered, 0.90)))),
        ),
        prob_up=_to_prob(sum(1 for value in ordered if value > 0) / samples),
        prob_hit={target: _to_prob(count / samples) for target, count in hits.items()},
        sample_size=samples,
        model_version=MODEL_VERSION,
    )
