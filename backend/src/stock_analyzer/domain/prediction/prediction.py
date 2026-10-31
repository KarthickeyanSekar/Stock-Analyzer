"""Prediction value objects: a return range plus target probabilities."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from stock_analyzer.domain.market.holding_category import HoldingCategory

# Targets (+N%) for which the probability of being reached is predicted.
TARGET_PCTS: tuple[int, ...] = (5, 10, 15, 20, 25, 30, 40, 50)


@dataclass(frozen=True, slots=True)
class ReturnRange:
    """Predicted return quantiles in percent points (p10 ≤ p50 ≤ p90)."""

    p10_pct: Decimal
    p50_pct: Decimal
    p90_pct: Decimal

    def __post_init__(self) -> None:
        """Reject a range whose quantiles are out of order."""
        if not self.p10_pct <= self.p50_pct <= self.p90_pct:
            raise ValueError("quantiles must satisfy p10 <= p50 <= p90")


@dataclass(frozen=True, slots=True)
class Prediction:
    """Prediction for one stock and holding category, made with data up to ``as_of``."""

    stock_id: int
    as_of: date
    category: HoldingCategory
    range: ReturnRange
    prob_up: Decimal
    # {target %: probability of reaching it before the stop-loss}
    prob_hit: dict[int, Decimal] = field(default_factory=dict)
    sample_size: int = 0
    model_version: str = ""
    id: int | None = None
