"""ML model registry entries and the distribution a model predicts (docs/26-ml-pipeline.md §6)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from stock_analyzer.domain.market.holding_category import HoldingCategory


class ModelStatus(StrEnum):
    """Lifecycle: CANDIDATE → ACTIVE → RETIRED; exactly one ACTIVE per category."""

    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


@dataclass(slots=True)
class ModelVersion:
    """One trained model (or the rule-based baseline when ``category`` is ``None``)."""

    name: str
    category: HoldingCategory | None
    algorithm: str
    status: ModelStatus = ModelStatus.CANDIDATE
    params: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    feature_set: str | None = None
    artifact_path: str | None = None
    trained_at: datetime | None = None
    activated_at: datetime | None = None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class PredictedDistribution:
    """A model's output for one sample: return quantiles in percent points and probabilities."""

    p10: float
    p50: float
    p90: float
    prob_up: float
    prob_hit: dict[int, float]
