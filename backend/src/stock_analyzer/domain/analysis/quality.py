"""Quality score 0-10 for the screener (Q67), from the features computed today.

Five components, 0-2 points each, mostly universe-relative (percentile ranks on the date):
ROE, revenue growth, earnings yield, low volatility, and debt/equity (absolute bands).
A missing input scores 0 points, so thin data never looks like quality.
"""

from collections.abc import Mapping

TOP, MIDDLE = 2 / 3, 1 / 3
LOW_DEBT, MODERATE_DEBT = 0.5, 1.0


def _rank_points(rank: float | None, *, higher_is_better: bool = True) -> int:
    if rank is None:
        return 0
    value = rank if higher_is_better else 1 - rank
    return 2 if value >= TOP else 1 if value >= MIDDLE else 0


def _debt_points(debt_to_equity: float | None) -> int:
    if debt_to_equity is None:
        return 0
    return 2 if debt_to_equity < LOW_DEBT else 1 if debt_to_equity < MODERATE_DEBT else 0


def quality_score(features: Mapping[str, float | None]) -> int:
    """Return the 0-10 quality score for one stock on one date."""
    return (
        _rank_points(features.get("roe_rank"))
        + _rank_points(features.get("revenue_yoy_rank"))
        + _rank_points(features.get("earnings_yield_rank"))
        + _rank_points(features.get("volatility_1y_rank"), higher_is_better=False)
        + _debt_points(features.get("debt_to_equity"))
    )
