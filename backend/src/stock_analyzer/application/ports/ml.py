"""ML engine ports: feature store, model registry and trainer (docs/26-ml-pipeline.md §11)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from stock_analyzer.domain.analysis.features import Features
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.labels import Label
from stock_analyzer.domain.prediction.model_version import ModelVersion, PredictedDistribution

FeatureRow = list[float | None]


@dataclass(frozen=True, slots=True)
class TrainingData:
    """Feature rows with their outcomes: forward return and target hits before the stop."""

    rows: Sequence[FeatureRow]
    returns_pct: Sequence[float]
    hits: Mapping[int, Sequence[bool]]


class FeatureRepository(Protocol):
    """Point-in-time features and training labels."""

    async def upsert_features(
        self, feature_set: str, rows: Sequence[tuple[int, date, Features]]
    ) -> int:
        """Insert or replace feature vectors; return how many were written."""
        ...

    async def load_features(self, feature_set: str) -> dict[tuple[int, date], Features]:
        """Return every stored vector of a feature set keyed by (stock id, date)."""
        ...

    async def latest_features(self, feature_set: str) -> dict[int, tuple[date, Features]]:
        """Return each stock's most recent feature vector."""
        ...

    async def upsert_labels(
        self, category: HoldingCategory, rows: Sequence[tuple[int, date, Label]]
    ) -> int:
        """Insert or replace labels; return how many were written."""
        ...

    async def load_labels(self, category: HoldingCategory) -> dict[tuple[int, date], Label]:
        """Return every label of a category keyed by (stock id, date)."""
        ...


class ModelRegistry(Protocol):
    """Model versions and which one is ACTIVE per category."""

    async def add(self, version: ModelVersion) -> ModelVersion:
        """Store a new version and return it with its id."""
        ...

    async def active(self, category: HoldingCategory) -> ModelVersion | None:
        """Return the category's ACTIVE ML model, or ``None`` (the baseline is used)."""
        ...

    async def activate(self, version_id: int, now: datetime) -> None:
        """Make the version ACTIVE and retire the category's previous ACTIVE one."""
        ...

    async def rollback(self, category: HoldingCategory, now: datetime) -> ModelVersion | None:
        """Retire the ACTIVE model and re-activate the most recently retired one."""
        ...

    async def list_for(self, category: HoldingCategory) -> list[ModelVersion]:
        """Return the category's versions, newest first."""
        ...


class TrainedModel(Protocol):
    """A fitted model that can predict and be saved."""

    def predict(self, rows: Sequence[FeatureRow]) -> list[PredictedDistribution]:
        """Return one calibrated distribution per feature row."""
        ...

    def save(self, path: str) -> None:
        """Write the model to ``path``."""
        ...


class ModelTrainer(Protocol):
    """Fits quantile + target-probability models with calibration (an ML library adapter)."""

    @property
    def algorithm(self) -> str:
        """Name stored on the model version (e.g., ``lightgbm-quantile``)."""
        ...

    @property
    def params(self) -> dict[str, float | int | str]:
        """Hyper-parameters stored on the model version."""
        ...

    def fit(self, train: TrainingData, calibration: TrainingData) -> TrainedModel:
        """Fit on the training rows; calibrate ranges and probabilities on a later slice."""
        ...

    def load(self, path: str) -> TrainedModel:
        """Load a model saved with :meth:`TrainedModel.save`."""
        ...
