"""Short-term setup label (Q77): a statistical summary, not advice (Q74)."""

from decimal import Decimal
from enum import StrEnum

from stock_analyzer.domain.prediction.prediction import Prediction

FAVOURABLE_CHANCE_UP = Decimal("0.55")
UNFAVOURABLE_CHANCE_UP = Decimal("0.45")
ROUND_TRIP_COST_PCT = Decimal("0.25")


class Setup(StrEnum):
    """How the odds look for a short hold."""

    FAVOURABLE = "FAVOURABLE"
    NEUTRAL = "NEUTRAL"
    UNFAVOURABLE = "UNFAVOURABLE"


def setup_of(prediction: Prediction) -> Setup:
    """Label the odds of a short hold.

    Favourable: chance up ≥ 55% and median above costs. Unfavourable: chance up ≤ 45% or a
    negative median. Otherwise neutral.
    """
    median = prediction.range.p50_pct
    if prediction.prob_up <= UNFAVOURABLE_CHANCE_UP or median < 0:
        return Setup.UNFAVOURABLE
    if prediction.prob_up >= FAVOURABLE_CHANCE_UP and median > ROUND_TRIP_COST_PCT:
        return Setup.FAVOURABLE
    return Setup.NEUTRAL
