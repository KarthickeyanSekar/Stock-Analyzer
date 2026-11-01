"""Holding-period screener rules (docs/16-holding-period-screener.md; Q66, Q68).

Pure functions over predictions: which target probability answers "I want X%", which rows
pass the filters, how they are ranked, and which holding period is best risk-adjusted.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS, Prediction


@dataclass(frozen=True, slots=True)
class ScreenCriteria:
    """What the user asks for: "N days, X% (to Y%)" plus optional filters."""

    category: HoldingCategory
    target_pct: int
    target_max_pct: int | None = None
    min_probability: Decimal = Decimal(0)
    min_worst_pct: Decimal | None = None  # Q66: p10 must be at least this (e.g., -8)
    min_quality: int = 0
    sectors: frozenset[str] = frozenset()


def target_level(target_pct: int) -> int | None:
    """Smallest predicted target ≥ the wish (probabilities exist for 5, 10, … 50%)."""
    return next((t for t in TARGET_PCTS if t >= target_pct), None)


@dataclass(frozen=True, slots=True)
class Candidate:
    """A stock's prediction with the facts the filters need."""

    symbol: str
    sector: str | None
    prediction: Prediction
    quality: int | None


def probability_of(prediction: Prediction, target_pct: int) -> Decimal | None:
    """Probability of reaching ``target_pct`` (at the next predicted level) before the stop."""
    level = target_level(target_pct)
    return prediction.prob_hit.get(level) if level is not None else None


def passes(candidate: Candidate, criteria: ScreenCriteria) -> bool:
    """Whether a candidate meets every filter."""
    p = candidate.prediction
    probability = probability_of(p, criteria.target_pct)
    return (
        p.category is criteria.category
        and probability is not None
        and probability >= criteria.min_probability
        and (criteria.min_worst_pct is None or p.range.p10_pct >= criteria.min_worst_pct)
        and (candidate.quality or 0) >= criteria.min_quality
        and (not criteria.sectors or candidate.sector in criteria.sectors)
    )


def screen(candidates: Sequence[Candidate], criteria: ScreenCriteria) -> list[Candidate]:
    """Filter, then rank by probability of the target, then median, then symbol."""
    matches = [c for c in candidates if passes(c, criteria)]
    return sorted(
        matches,
        key=lambda c: (
            -(probability_of(c.prediction, criteria.target_pct) or Decimal(0)),
            -c.prediction.range.p50_pct,
            c.symbol,
        ),
    )


def risk_adjusted(prediction: Prediction) -> Decimal | None:
    """Q68: median ÷ downside (p50 - p10); ``None`` unless the median is positive."""
    r = prediction.range
    downside = r.p50_pct - r.p10_pct
    if r.p50_pct <= 0 or downside <= 0:
        return None
    return r.p50_pct / downside


def best_category(predictions: Sequence[Prediction]) -> HoldingCategory | None:
    """The holding period with the best risk-adjusted outlook (ties → shorter period)."""
    order = list(HoldingCategory)
    scored = [(score, p.category) for p in predictions if (score := risk_adjusted(p)) is not None]
    if not scored:
        return None
    return max(scored, key=lambda item: (item[0], -order.index(item[1])))[1]
