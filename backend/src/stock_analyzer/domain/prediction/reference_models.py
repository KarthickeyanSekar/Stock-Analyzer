"""Reference models the ML engine must beat (docs/26-ml-pipeline.md §4 "Baselines").

- ``UniverseBaseline``: the historical distribution of every stock's outcomes (no features).
- ``MomentumBaseline``: the same, split into terciles of 12-1 month momentum rank.
Both are fitted on the training fold only, like the ML model.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from stock_analyzer.domain.prediction.baseline import _quantile
from stock_analyzer.domain.prediction.evaluation import QUANTILES
from stock_analyzer.domain.prediction.model_version import PredictedDistribution

MOMENTUM_FEATURE = "mom_12_1m_rank"
TERCILES = (1 / 3, 2 / 3)


def _distribution(
    returns: Sequence[float], hits: Mapping[int, Sequence[bool]]
) -> PredictedDistribution:
    ordered = sorted(returns)
    p10, p50, p90 = (_quantile(ordered, q) for q in QUANTILES)
    n = len(ordered)
    return PredictedDistribution(
        p10=p10,
        p50=p50,
        p90=p90,
        prob_up=sum(r > 0 for r in ordered) / n,
        prob_hit={t: sum(values) / n for t, values in hits.items()},
    )


@dataclass(frozen=True, slots=True)
class UniverseBaseline:
    """Same distribution for every stock: what happened across the universe in training."""

    distribution: PredictedDistribution

    @classmethod
    def fit(
        cls, returns: Sequence[float], hits: Mapping[int, Sequence[bool]]
    ) -> "UniverseBaseline":
        """Fit on training outcomes."""
        return cls(_distribution(returns, hits))

    def predict(self, momentum_ranks: Sequence[float | None]) -> list[PredictedDistribution]:
        """One (identical) distribution per sample."""
        return [self.distribution] * len(momentum_ranks)


def _bucket(rank: float | None) -> int | None:
    if rank is None:
        return None
    return sum(rank > edge for edge in TERCILES)


@dataclass(frozen=True, slots=True)
class MomentumBaseline:
    """Distribution conditional on the momentum tercile (falls back to the universe)."""

    by_bucket: dict[int, PredictedDistribution]
    fallback: PredictedDistribution

    @classmethod
    def fit(
        cls,
        momentum_ranks: Sequence[float | None],
        returns: Sequence[float],
        hits: Mapping[int, Sequence[bool]],
    ) -> "MomentumBaseline":
        """Fit one distribution per momentum tercile on training outcomes."""
        by_bucket: dict[int, PredictedDistribution] = {}
        for bucket in range(len(TERCILES) + 1):
            index = [i for i, r in enumerate(momentum_ranks) if _bucket(r) == bucket]
            if index:
                by_bucket[bucket] = _distribution(
                    [returns[i] for i in index],
                    {t: [values[i] for i in index] for t, values in hits.items()},
                )
        return cls(by_bucket, _distribution(returns, hits))

    def predict(self, momentum_ranks: Sequence[float | None]) -> list[PredictedDistribution]:
        """Distribution of each sample's tercile."""
        result = []
        for rank in momentum_ranks:
            bucket = _bucket(rank)
            result.append(
                self.by_bucket.get(bucket, self.fallback) if bucket is not None else self.fallback
            )
        return result
