"""LightGBM quantile + target-probability models with calibration (docs/26-ml-pipeline.md §4).

- Ranges: three quantile models (p10/p50/p90), widened or narrowed by a split-conformal margin
  measured on a later calibration slice, so the 80% range really covers ~80%.
- Probabilities: one binary model per target (and one for "ends up"), mapped through isotonic
  regression fitted on the calibration slice; probabilities never rise as the target rises.
"""

import pickle
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import lightgbm as lgb
import numpy as np
from sklearn.isotonic import IsotonicRegression

from stock_analyzer.application.ports.ml import FeatureRow, TrainingData
from stock_analyzer.domain.prediction.evaluation import QUANTILES, conformal_margin
from stock_analyzer.domain.prediction.model_version import PredictedDistribution

ALGORITHM = "lightgbm-quantile-isotonic"
UP = 0  # key of the "ends higher" classifier next to the target %s
BASE_PARAMS: dict[str, float | int | str] = {
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "num_threads": 2,
    "deterministic": "true",
    "seed": 42,
    "verbose": -1,
}
ROUNDS = 200


def _matrix(rows: Sequence[FeatureRow]) -> np.ndarray:
    """Rows with ``None`` → NaN (LightGBM handles missing values natively)."""
    matrix: np.ndarray = np.array(
        [[np.nan if v is None else v for v in row] for row in rows], dtype=float
    )
    return matrix


@dataclass(slots=True)
class _Classifier:
    """A booster plus its isotonic map, or a constant when training saw only one class."""

    booster: lgb.Booster | None = None
    isotonic: IsotonicRegression | None = None
    constant: float = 0.0

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.booster is None:
            return np.full(len(x), self.constant)
        raw = self.booster.predict(x)
        calibrated = self.isotonic.predict(raw) if self.isotonic is not None else raw
        probs: np.ndarray = np.clip(np.asarray(calibrated, dtype=float), 0.0, 1.0)
        return probs


@dataclass(slots=True)
class LightGbmModel:
    """Fitted quantile boosters, calibrated classifiers and the conformal margin."""

    quantiles: dict[float, lgb.Booster]
    classifiers: dict[int, _Classifier]
    margin: float
    targets: tuple[int, ...] = field(default=())

    def predict(self, rows: Sequence[FeatureRow]) -> list[PredictedDistribution]:
        """Calibrated distribution per row (quantiles sorted, probabilities monotone)."""
        x = _matrix(rows)
        raw = np.sort(np.column_stack([self.quantiles[q].predict(x) for q in QUANTILES]), axis=1)
        low, high = raw[:, 0] - self.margin, raw[:, 2] + self.margin
        mid = np.clip(raw[:, 1], np.minimum(low, high), np.maximum(low, high))
        low, high = np.minimum(low, mid), np.maximum(high, mid)
        up = self.classifiers[UP].predict(x)
        hits = np.column_stack([self.classifiers[t].predict(x) for t in self.targets])
        hits = np.minimum.accumulate(hits, axis=1)  # P(+20%) ≤ P(+10%)
        return [
            PredictedDistribution(
                p10=float(low[i]),
                p50=float(mid[i]),
                p90=float(high[i]),
                prob_up=float(up[i]),
                prob_hit={t: float(hits[i, j]) for j, t in enumerate(self.targets)},
            )
            for i in range(len(rows))
        ]

    def save(self, path: str) -> None:
        """Pickle the model (files are written and read only by this app, in its own volume)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("wb") as handle:
            pickle.dump(self, handle)


class LightGbmTrainer:
    """Trains :class:`LightGbmModel` instances (implements ``ModelTrainer``)."""

    def __init__(self, rounds: int = ROUNDS) -> None:
        """Use ``rounds`` boosting rounds per model."""
        self._rounds = rounds

    @property
    def algorithm(self) -> str:
        """Name stored on the model version."""
        return ALGORITHM

    @property
    def params(self) -> dict[str, float | int | str]:
        """Hyper-parameters stored on the model version."""
        return BASE_PARAMS | {"rounds": self._rounds}

    def _train(self, x: np.ndarray, y: np.ndarray, extra: dict[str, float | str]) -> lgb.Booster:
        return lgb.train(BASE_PARAMS | extra, lgb.Dataset(x, label=y), num_boost_round=self._rounds)

    def _classifier(
        self, x: np.ndarray, y: np.ndarray, x_cal: np.ndarray, y_cal: np.ndarray
    ) -> _Classifier:
        if y.min() == y.max():
            return _Classifier(constant=float(y[0]))
        booster = self._train(x, y, {"objective": "binary"})
        isotonic = None
        if len(y_cal) and y_cal.min() != y_cal.max():
            isotonic = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            isotonic.fit(booster.predict(x_cal), y_cal)
        return _Classifier(booster=booster, isotonic=isotonic)

    def fit(self, train: TrainingData, calibration: TrainingData) -> LightGbmModel:
        """Fit on the training rows; calibrate on the (later, purged) calibration slice."""
        x, y = _matrix(train.rows), np.array(train.returns_pct, dtype=float)
        x_cal = _matrix(calibration.rows)
        y_cal = np.array(calibration.returns_pct, dtype=float)
        hits, calibration_hits = train.hits, calibration.hits
        quantiles = {q: self._train(x, y, {"objective": "quantile", "alpha": q}) for q in QUANTILES}
        margin = 0.0
        if len(y_cal):
            raw = np.sort(np.column_stack([quantiles[q].predict(x_cal) for q in QUANTILES]), axis=1)
            margin = conformal_margin(list(y_cal), list(raw[:, 0]), list(raw[:, 2]))
        targets = tuple(sorted(hits))
        classifiers = {
            UP: self._classifier(x, (y > 0).astype(float), x_cal, (y_cal > 0).astype(float))
        }
        for target in targets:
            classifiers[target] = self._classifier(
                x,
                np.array(hits[target], dtype=float),
                x_cal,
                np.array(calibration_hits.get(target, []), dtype=float),
            )
        return LightGbmModel(quantiles, classifiers, margin, targets)

    def load(self, path: str) -> LightGbmModel:
        """Load a model this app saved (trusted file in its own models volume)."""
        with Path(path).open("rb") as handle:
            model: LightGbmModel = pickle.load(handle)  # noqa: S301 - own artifact, not user input
        return model
