"""SQLAlchemy prediction repository."""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.prediction import Prediction, ReturnRange
from stock_analyzer.infrastructure.persistence.models import ModelVersionModel, PredictionModel


class SqlAlchemyPredictionRepository:
    """Predictions and their model versions."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def _model_version_id(self, name: str, algorithm: str) -> int:
        # Look up first: category is NULL for all-category models, and NULLs never conflict
        # in a unique constraint, so INSERT ... ON CONFLICT would create duplicates.
        version_id = await self._session.scalar(
            select(ModelVersionModel.id).where(
                ModelVersionModel.name == name, ModelVersionModel.category.is_(None)
            )
        )
        if version_id is not None:
            return version_id
        version = ModelVersionModel(name=name, category=None, algorithm=algorithm, status="ACTIVE")
        self._session.add(version)
        await self._session.flush()
        return version.id

    async def save_many(self, predictions: Sequence[Prediction], algorithm: str) -> int:
        """Replace predictions for the same stock, date, category and model; return count."""
        if not predictions:
            return 0
        version_ids: dict[str, int] = {}
        for name in {p.model_version for p in predictions}:
            version_ids[name] = await self._model_version_id(name, algorithm)
        rows = [
            {
                "stock_id": p.stock_id,
                "as_of": p.as_of,
                "category": p.category.value,
                "p10_pct": p.range.p10_pct,
                "p50_pct": p.range.p50_pct,
                "p90_pct": p.range.p90_pct,
                "prob_up": p.prob_up,
                "prob_hit": {str(target): str(prob) for target, prob in p.prob_hit.items()},
                "model_version_id": version_ids[p.model_version],
            }
            for p in predictions
        ]
        statement = insert(PredictionModel).values(rows)
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=["stock_id", "as_of", "category", "model_version_id"],
                set_={
                    column: statement.excluded[column]
                    for column in ("p10_pct", "p50_pct", "p90_pct", "prob_up", "prob_hit")
                },
            )
        )
        return len(rows)

    async def latest_for_stock(self, stock_id: int) -> list[Prediction]:
        """Return the newest prediction per holding category."""
        statement = (
            select(PredictionModel, ModelVersionModel.name)
            .join(ModelVersionModel, PredictionModel.model_version_id == ModelVersionModel.id)
            .where(PredictionModel.stock_id == stock_id)
            .distinct(PredictionModel.category)
            .order_by(PredictionModel.category, PredictionModel.as_of.desc())
        )
        result = await self._session.execute(statement)
        predictions = [
            Prediction(
                stock_id=row.stock_id,
                as_of=row.as_of,
                category=HoldingCategory(row.category),
                range=ReturnRange(row.p10_pct, row.p50_pct, row.p90_pct),
                prob_up=row.prob_up,
                prob_hit={int(t): Decimal(p) for t, p in row.prob_hit.items()},
                model_version=name,
                id=row.id,
            )
            for row, name in result.tuples()
        ]
        order = list(HoldingCategory)
        return sorted(predictions, key=lambda p: order.index(p.category))
