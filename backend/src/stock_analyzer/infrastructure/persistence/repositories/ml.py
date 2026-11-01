"""SQLAlchemy feature store, label store and model registry."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.analysis.features import Features
from stock_analyzer.domain.market.holding_category import HoldingCategory
from stock_analyzer.domain.prediction.labels import Label
from stock_analyzer.domain.prediction.model_version import ModelStatus, ModelVersion
from stock_analyzer.infrastructure.persistence.models import (
    FeatureDailyModel,
    LabelDailyModel,
    ModelVersionModel,
)

BATCH_SIZE = 2000


class SqlAlchemyFeatureRepository:
    """``features_daily`` and ``labels_daily``."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def upsert_features(
        self, feature_set: str, rows: Sequence[tuple[int, date, Features]]
    ) -> int:
        """Insert or replace feature vectors in batches."""
        for offset in range(0, len(rows), BATCH_SIZE):
            values = [
                {"stock_id": s, "as_of": d, "feature_set": feature_set, "values": f}
                for s, d, f in rows[offset : offset + BATCH_SIZE]
            ]
            statement = insert(FeatureDailyModel).values(values)
            await self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=["stock_id", "as_of", "feature_set"],
                    set_={"values": statement.excluded["values"]},
                )
            )
        return len(rows)

    async def load_features(self, feature_set: str) -> dict[tuple[int, date], Features]:
        """Return every vector of a feature set keyed by (stock id, date)."""
        rows = await self._session.scalars(
            select(FeatureDailyModel).where(FeatureDailyModel.feature_set == feature_set)
        )
        return {(r.stock_id, r.as_of): dict(r.values) for r in rows}

    async def latest_features(self, feature_set: str) -> dict[int, tuple[date, Features]]:
        """Return each stock's most recent vector."""
        rows = await self._session.scalars(
            select(FeatureDailyModel)
            .where(FeatureDailyModel.feature_set == feature_set)
            .distinct(FeatureDailyModel.stock_id)
            .order_by(FeatureDailyModel.stock_id, FeatureDailyModel.as_of.desc())
        )
        return {r.stock_id: (r.as_of, dict(r.values)) for r in rows}

    async def upsert_labels(
        self, category: HoldingCategory, rows: Sequence[tuple[int, date, Label]]
    ) -> int:
        """Insert or replace labels in batches."""
        for offset in range(0, len(rows), BATCH_SIZE):
            values = [
                {
                    "stock_id": s,
                    "as_of": d,
                    "category": category.value,
                    "forward_return_pct": label.forward_return_pct,
                    "is_stopped": label.is_stopped,
                    "hits": {str(t): hit for t, hit in label.hits.items()},
                }
                for s, d, label in rows[offset : offset + BATCH_SIZE]
            ]
            statement = insert(LabelDailyModel).values(values)
            await self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=["stock_id", "as_of", "category"],
                    set_={
                        c: statement.excluded[c]
                        for c in ("forward_return_pct", "is_stopped", "hits")
                    },
                )
            )
        return len(rows)

    async def load_labels(self, category: HoldingCategory) -> dict[tuple[int, date], Label]:
        """Return every label of a category keyed by (stock id, date)."""
        rows = await self._session.scalars(
            select(LabelDailyModel).where(LabelDailyModel.category == category.value)
        )
        return {
            (r.stock_id, r.as_of): Label(
                forward_return_pct=r.forward_return_pct,
                is_stopped=r.is_stopped,
                hits={int(t): bool(h) for t, h in r.hits.items()},
            )
            for r in rows
        }


def _to_domain(row: ModelVersionModel) -> ModelVersion:
    return ModelVersion(
        id=row.id,
        name=row.name,
        category=HoldingCategory(row.category) if row.category else None,
        algorithm=row.algorithm,
        status=ModelStatus(row.status),
        params=dict(row.params),
        metrics=dict(row.metrics),
        feature_set=row.feature_set,
        artifact_path=row.artifact_path,
        trained_at=row.trained_at,
        activated_at=row.activated_at,
    )


class SqlAlchemyModelRegistry:
    """``model_versions``: one ACTIVE ML model per category (enforced by a unique index)."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def add(self, version: ModelVersion) -> ModelVersion:
        """Store a new CANDIDATE (or other status) version."""
        row = ModelVersionModel(
            name=version.name,
            category=version.category.value if version.category else None,
            algorithm=version.algorithm,
            status=version.status.value,
            params=version.params,
            metrics=version.metrics,
            feature_set=version.feature_set,
            artifact_path=version.artifact_path,
        )
        self._session.add(row)
        await self._session.flush()
        version.id, version.trained_at = row.id, row.trained_at
        return version

    async def active(self, category: HoldingCategory) -> ModelVersion | None:
        """Return the category's ACTIVE ML model, or ``None``."""
        row = await self._session.scalar(
            select(ModelVersionModel).where(
                ModelVersionModel.category == category.value,
                ModelVersionModel.status == ModelStatus.ACTIVE.value,
            )
        )
        return _to_domain(row) if row else None

    async def activate(self, version_id: int, now: datetime) -> None:
        """Retire the current ACTIVE version of the category, then activate this one."""
        row = await self._session.get(ModelVersionModel, version_id)
        if row is None or row.category is None:
            raise LookupError(f"model version {version_id} not found")
        await self._session.execute(
            update(ModelVersionModel)
            .where(
                ModelVersionModel.category == row.category,
                ModelVersionModel.status == ModelStatus.ACTIVE.value,
            )
            .values(status=ModelStatus.RETIRED.value)
        )
        await self._session.flush()
        row.status, row.activated_at = ModelStatus.ACTIVE.value, now
        await self._session.flush()

    async def rollback(self, category: HoldingCategory, now: datetime) -> ModelVersion | None:
        """Re-activate the most recently retired version (by activation time)."""
        current = await self.active(category)
        previous = await self._session.scalar(
            select(ModelVersionModel)
            .where(
                ModelVersionModel.category == category.value,
                ModelVersionModel.status == ModelStatus.RETIRED.value,
                ModelVersionModel.activated_at.is_not(None),
            )
            .order_by(ModelVersionModel.activated_at.desc())
            .limit(1)
        )
        if previous is None:
            return None
        if current and current.id is not None:
            current_row = await self._session.get(ModelVersionModel, current.id)
            if current_row is not None:
                current_row.status = ModelStatus.RETIRED.value
                await self._session.flush()
        previous.status, previous.activated_at = ModelStatus.ACTIVE.value, now
        await self._session.flush()
        return _to_domain(previous)

    async def list_for(self, category: HoldingCategory) -> list[ModelVersion]:
        """Return the category's versions, newest first."""
        rows = await self._session.scalars(
            select(ModelVersionModel)
            .where(ModelVersionModel.category == category.value)
            .order_by(ModelVersionModel.trained_at.desc(), ModelVersionModel.id.desc())
        )
        return [_to_domain(r) for r in rows]
