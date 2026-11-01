"""ML engine ORM models: feature store and training labels (docs/26-ml-pipeline.md)."""

from datetime import date
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, Date, Double, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stock_analyzer.domain.analysis.features import EMBEDDING_FEATURES
from stock_analyzer.infrastructure.persistence.models.base import Base
from stock_analyzer.infrastructure.persistence.models.prediction import HOLDING_CATEGORIES_SQL


class FeatureDailyModel(Base):
    """One point-in-time feature vector per stock, date and feature-set version."""

    __tablename__ = "features_daily"
    __table_args__ = (
        # Approximate nearest-neighbour search for similar past setups (cosine distance).
        Index(
            "ix_features_daily_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    as_of: Mapped[date] = mapped_column(Date, primary_key=True)
    feature_set: Mapped[str] = mapped_column(String(16), primary_key=True)
    # {feature name: value or null}; floats by design (Q64).
    values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(len(EMBEDDING_FEATURES)))


class LabelDailyModel(Base):
    """What happened after a date for one holding category (training target)."""

    __tablename__ = "labels_daily"
    __table_args__ = (CheckConstraint(f"category IN {HOLDING_CATEGORIES_SQL}", name="category"),)

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    as_of: Mapped[date] = mapped_column(Date, primary_key=True)
    category: Mapped[str] = mapped_column(String(4), primary_key=True)
    forward_return_pct: Mapped[float] = mapped_column(Double)
    is_stopped: Mapped[bool] = mapped_column(Boolean)
    # {target %: reached before the stop}
    hits: Mapped[dict[str, Any]] = mapped_column(JSONB)
