"""Train, evaluate and (only if every gate passes) activate ML models per holding category.

For each category (docs/26-ml-pipeline.md §5):
1. Join stored features and labels; order samples by date.
2. Purged walk-forward: for every fold, fit the candidate and both reference models on the
   training dates only (the candidate is calibrated on the latest training slice, purged by
   the holding period), then score all of them on the fold's test dates.
3. Apply the quality gates (Q51). Register the candidate with its scores and gate report.
4. Fit the final model on all dates; it becomes ACTIVE only if the gates passed.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from stock_analyzer.application.ports.clock import Clock
from stock_analyzer.application.ports.ml import (
    FeatureRow,
    ModelTrainer,
    TrainedModel,
    TrainingData,
)
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.application.use_cases.ml.build_features import SAMPLE_STEP
from stock_analyzer.domain.analysis.features import ALL_FEATURES, FEATURE_SET_VERSION, Features
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction import evaluation as ev
from stock_analyzer.domain.prediction.labels import Label
from stock_analyzer.domain.prediction.model_version import (
    ModelStatus,
    ModelVersion,
    PredictedDistribution,
)
from stock_analyzer.domain.prediction.prediction import TARGET_PCTS
from stock_analyzer.domain.prediction.reference_models import (
    MOMENTUM_FEATURE,
    MomentumBaseline,
    UniverseBaseline,
)

N_FOLDS = 4
MIN_FIT_DATES = 26  # half a year of weekly samples
CALIBRATION_SHARE = 0.25


@dataclass(frozen=True, slots=True)
class Sample:
    """One (stock, date) training example."""

    stock_id: int
    as_of: date
    row: FeatureRow
    momentum_rank: float | None
    label: Label


@dataclass(slots=True)
class CategoryResult:
    """What training did for one category."""

    category: HoldingCategory
    samples: int
    version: ModelVersion | None
    gates: ev.GateReport
    folds: list[dict[str, float | str]] = field(default_factory=list)

    @property
    def activated(self) -> bool:
        """Whether the new model became ACTIVE."""
        return self.version is not None and self.version.status is ModelStatus.ACTIVE


def embargo_dates(category: HoldingCategory, step: int = SAMPLE_STEP) -> int:
    """Holding period expressed in sample dates (+1 for safety)."""
    return math.ceil(category.approx_trading_days / step) + 1


def assemble(
    features: dict[tuple[int, date], Features], labels: dict[tuple[int, date], Label]
) -> list[Sample]:
    """Samples that have both features and a label, in date order."""
    samples = [
        Sample(
            stock_id=key[0],
            as_of=key[1],
            row=[features[key].get(name) for name in ALL_FEATURES],
            momentum_rank=features[key].get(MOMENTUM_FEATURE),
            label=label,
        )
        for key, label in labels.items()
        if key in features
    ]
    return sorted(samples, key=lambda s: (s.as_of, s.stock_id))


def score(dists: Sequence[PredictedDistribution], samples: Sequence[Sample]) -> ev.FoldScore:
    """Score predictions against what happened."""
    actual = [s.label.forward_return_pct for s in samples]
    outcomes: list[bool] = []
    probs: list[float] = []
    for d, s in zip(dists, samples, strict=True):
        outcomes.append(s.label.forward_return_pct > 0)
        probs.append(d.prob_up)
        for target in TARGET_PCTS:
            outcomes.append(s.label.hits[target])
            probs.append(d.prob_hit[target])
    return ev.FoldScore(
        pinball=ev.mean_pinball(
            actual, [[d.p10 for d in dists], [d.p50 for d in dists], [d.p90 for d in dists]]
        ),
        coverage=ev.coverage(actual, [d.p10 for d in dists], [d.p90 for d in dists]),
        ece_pp=ev.expected_calibration_error(outcomes, probs),
        direction_accuracy=ev.direction_accuracy(actual, [d.p50 for d in dists]),
        samples=len(samples),
    )


def _hits(samples: Sequence[Sample]) -> dict[int, Sequence[bool]]:
    return {t: [s.label.hits[t] for s in samples] for t in TARGET_PCTS}


def _data(samples: Sequence[Sample]) -> TrainingData:
    return TrainingData(
        rows=[s.row for s in samples],
        returns_pct=[s.label.forward_return_pct for s in samples],
        hits=_hits(samples),
    )


class TrainHoldingPeriodModels:
    """Weekly training job (``make train``)."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        trainer: ModelTrainer,
        clock: Clock,
        models_dir: str,
        code_version: str = "unknown",
    ) -> None:
        """Train with ``trainer``; model files go under ``models_dir``."""
        self._uow_factory = uow_factory
        self._trainer = trainer
        self._clock = clock
        self._models_dir = models_dir
        self._code_version = code_version

    def _fit(self, samples: Sequence[Sample], embargo: int) -> TrainedModel | None:
        """Fit on the older part, calibrate on the latest dates, purged by ``embargo``."""
        dates = sorted({s.as_of for s in samples})
        n_cal = max(1, int(len(dates) * CALIBRATION_SHARE))
        fit_dates = dates[: len(dates) - n_cal - embargo]
        if len(fit_dates) < MIN_FIT_DATES:
            return None
        cal_start, fit_end = dates[len(dates) - n_cal], fit_dates[-1]
        fit = [s for s in samples if s.as_of <= fit_end]
        cal = [s for s in samples if s.as_of >= cal_start]
        return self._trainer.fit(_data(fit), _data(cal))

    def walk_forward(
        self, samples: Sequence[Sample], category: HoldingCategory
    ) -> tuple[list[ev.FoldScore], Mapping[str, list[ev.FoldScore]], list[dict[str, float | str]]]:
        """Candidate and baseline scores on every purged walk-forward fold."""
        embargo = embargo_dates(category)
        folds = ev.walk_forward_folds(
            [s.as_of for s in samples],
            N_FOLDS,
            embargo,
            min_train=MIN_FIT_DATES + embargo + int(MIN_FIT_DATES * CALIBRATION_SHARE) + 1,
        )
        candidate: list[ev.FoldScore] = []
        baselines: dict[str, list[ev.FoldScore]] = {"universe": [], "momentum": []}
        report: list[dict[str, float | str]] = []
        for fold in folds:
            train = [s for s in samples if s.as_of < fold.train_end]
            test = [s for s in samples if fold.test_start <= s.as_of <= fold.test_end]
            model = self._fit(train, embargo)
            if model is None or not test:
                continue
            ranks = [s.momentum_rank for s in test]
            returns = [s.label.forward_return_pct for s in train]
            universe = UniverseBaseline.fit(returns, _hits(train))
            momentum = MomentumBaseline.fit([s.momentum_rank for s in train], returns, _hits(train))
            scored = score(model.predict([s.row for s in test]), test)
            candidate.append(scored)
            baselines["universe"].append(score(universe.predict(ranks), test))
            baselines["momentum"].append(score(momentum.predict(ranks), test))
            report.append(
                {
                    "test_start": fold.test_start.isoformat(),
                    "test_end": fold.test_end.isoformat(),
                    "samples": scored.samples,
                    "pinball": round(scored.pinball, 4),
                    "pinball_universe": round(baselines["universe"][-1].pinball, 4),
                    "pinball_momentum": round(baselines["momentum"][-1].pinball, 4),
                    "coverage": round(scored.coverage, 4),
                    "ece_pp": round(scored.ece_pp, 2),
                    "direction_accuracy": round(scored.direction_accuracy, 4),
                }
            )
        return candidate, baselines, report

    async def execute(
        self, categories: Sequence[HoldingCategory] = tuple(HoldingCategory)
    ) -> list[CategoryResult]:
        """Train every category; return what happened to each."""
        async with self._uow_factory() as uow:
            features = await uow.features.load_features(FEATURE_SET_VERSION)
        results = []
        for category in categories:
            async with self._uow_factory() as uow:
                labels = await uow.features.load_labels(category)
                current = await uow.models.active(category)
            samples = assemble(features, labels)
            candidate, baselines, folds = self.walk_forward(samples, category)
            current_scores = None
            if current and "pinball" in current.metrics.get("gates", {}).get("details", {}):
                pinball = float(current.metrics["gates"]["details"]["pinball"])
                current_scores = [ev.FoldScore(pinball, 0.0, 0.0, 0.0, 0)]
            gates = ev.evaluate_gates(candidate, baselines, current_scores)
            result = CategoryResult(category, len(samples), None, gates, folds)
            final = self._fit(samples, embargo_dates(category)) if candidate else None
            if final is not None:
                result.version = await self._register(category, final, gates, folds, samples)
            results.append(result)
        return results

    async def _register(
        self,
        category: HoldingCategory,
        model: TrainedModel,
        gates: ev.GateReport,
        folds: list[dict[str, float | str]],
        samples: Sequence[Sample],
    ) -> ModelVersion:
        now = self._clock.now()
        name = f"lgbm-{category.value}-{now:%Y%m%d%H%M%S}"
        artifact = f"{category.value}/{name}.pkl"
        model.save(str(Path(self._models_dir) / artifact))
        version = ModelVersion(
            name=name,
            category=category,
            algorithm=self._trainer.algorithm,
            params=dict(self._trainer.params)
            | {
                "samples": len(samples),
                "data_end": samples[-1].as_of.isoformat(),
                "code_version": self._code_version,
            },
            metrics={
                "gates": {"passed": gates.passed, "checks": gates.checks, "details": gates.details},
                "folds": folds,
            },
            feature_set=FEATURE_SET_VERSION,
            artifact_path=artifact,
        )
        async with self._uow_factory() as uow:
            version = await uow.models.add(version)
            if gates.passed and version.id is not None:
                await uow.models.activate(version.id, now)
                version.status, version.activated_at = ModelStatus.ACTIVE, now
            await uow.commit()
        return version
