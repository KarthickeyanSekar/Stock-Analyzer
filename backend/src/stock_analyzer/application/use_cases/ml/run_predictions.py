"""Nightly predictions (``make predict``): the ACTIVE ML model per category, else the baseline.

Every prediction stores the model version that made it (docs/26-ml-pipeline.md §7).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from stock_analyzer.application.ports.ml import ModelTrainer, TrainedModel
from stock_analyzer.application.ports.repositories import UnitOfWorkFactory
from stock_analyzer.domain.analysis.features import ALL_FEATURES
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.baseline import empirical_prediction
from stock_analyzer.domain.prediction.model_version import ModelVersion, PredictedDistribution
from stock_analyzer.domain.prediction.prediction import Prediction, ReturnRange
from stock_analyzer.domain.shared.percent import round_pct

BASELINE_ALGORITHM = "empirical-forward-returns"
MAX_STOCKS = 10_000
PROB_PLACES = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class PredictionRun:
    """How many predictions each kind of model produced."""

    ml: int
    baseline: int


def _decimal(value: float) -> Decimal:
    return round_pct(Decimal(str(value)))


def _prob(value: float) -> Decimal:
    return Decimal(str(min(1.0, max(0.0, value)))).quantize(PROB_PLACES)


def to_prediction(
    stock_id: int,
    category: HoldingCategory,
    as_of_date: date,
    dist: PredictedDistribution,
    name: str,
) -> Prediction:
    """Round a model's float distribution into the stored Decimal prediction (Q64)."""
    return Prediction(
        stock_id=stock_id,
        as_of=as_of_date,
        category=category,
        range=ReturnRange(_decimal(dist.p10), _decimal(dist.p50), _decimal(dist.p90)),
        prob_up=_prob(dist.prob_up),
        prob_hit={t: _prob(p) for t, p in dist.prob_hit.items()},
        model_version=name,
    )


class RunPredictions:
    """Predict every stock x category with the best available model."""

    def __init__(
        self, uow_factory: UnitOfWorkFactory, trainer: ModelTrainer, models_dir: str
    ) -> None:
        """Load ACTIVE models with ``trainer`` from ``models_dir``."""
        self._uow_factory = uow_factory
        self._trainer = trainer
        self._models_dir = models_dir

    async def execute(self) -> PredictionRun:
        """Store one prediction per stock and category; return the counts."""
        active: dict[HoldingCategory, tuple[ModelVersion, TrainedModel]] = {}
        async with self._uow_factory() as uow:
            for category in HoldingCategory:
                version = await uow.models.active(category)
                if version and version.artifact_path and version.feature_set:
                    path = Path(self._models_dir) / version.artifact_path
                    if path.exists():
                        active[category] = (version, self._trainer.load(str(path)))
            latest = {}
            feature_sets = {v.feature_set for v, _ in active.values() if v.feature_set}
            for feature_set in feature_sets:
                latest[feature_set] = await uow.features.latest_features(feature_set)
            stocks = await uow.stocks.search(None, MAX_STOCKS)

        ml = baseline = 0
        for stock in stocks:
            if stock.id is None:  # pragma: no cover
                continue
            async with self._uow_factory() as uow:
                candles = await uow.prices.get_candles(stock.id)
                if not candles:
                    continue
                last_day = candles[-1].trade_date
                ml_predictions: list[Prediction] = []
                base_predictions: list[Prediction] = []
                for category in HoldingCategory:
                    model = active.get(category)
                    vector = (
                        latest.get(model[0].feature_set or "", {}).get(stock.id) if model else None
                    )
                    if model and vector and vector[0] == last_day:
                        row = [vector[1].get(name) for name in ALL_FEATURES]
                        dist = model[1].predict([row])[0]
                        ml_predictions.append(
                            to_prediction(stock.id, category, last_day, dist, model[0].name)
                        )
                    elif fallback := empirical_prediction(
                        stock_id=stock.id,
                        as_of=last_day,
                        category=category,
                        closes=[(c.trade_date, c.adj_close) for c in candles],
                    ):
                        base_predictions.append(fallback)
                ml += await uow.predictions.save_many(ml_predictions, "lightgbm")
                baseline += await uow.predictions.save_many(base_predictions, BASELINE_ALGORITHM)
                await uow.commit()
        return PredictionRun(ml=ml, baseline=baseline)
