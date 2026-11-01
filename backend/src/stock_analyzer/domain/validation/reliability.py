"""Reliability table: does "41% chance" happen about 41% of the time? (doc 12 §6)."""

from collections.abc import Sequence
from dataclasses import dataclass

BUCKETS = 10


@dataclass(frozen=True, slots=True)
class ReliabilityRow:
    """One probability bucket."""

    low: float
    high: float
    count: int
    mean_predicted: float
    observed: float


def reliability(outcomes: Sequence[bool], probs: Sequence[float]) -> list[ReliabilityRow]:
    """Non-empty 10%-wide buckets with predicted vs observed frequency."""
    groups: list[list[tuple[bool, float]]] = [[] for _ in range(BUCKETS)]
    for hit, prob in zip(outcomes, probs, strict=True):
        groups[min(int(prob * BUCKETS), BUCKETS - 1)].append((hit, prob))
    return [
        ReliabilityRow(
            low=i / BUCKETS,
            high=(i + 1) / BUCKETS,
            count=len(g),
            mean_predicted=sum(p for _, p in g) / len(g),
            observed=sum(h for h, _ in g) / len(g),
        )
        for i, g in enumerate(groups)
        if g
    ]
