"""SQLAlchemy repositories for plan tracking snapshots and journal settings."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from stock_analyzer.domain.journal.progress import PlanProgress
from stock_analyzer.domain.journal.settings import JournalSettings
from stock_analyzer.infrastructure.persistence.models import (
    JournalSettingsModel,
    PlanDailyStatusModel,
)

SNAPSHOT_COLUMNS = (
    "close",
    "return_pct",
    "progress_pct",
    "day_number",
    "total_days",
    "target_reached_on",
    "stop_hit_on",
    "is_end_date_reached",
)


class SqlAlchemyPlanStatusRepository:
    """Daily plan snapshots in ``plan_daily_status``."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    async def upsert_many(self, plan_id: int, snapshots: Sequence[PlanProgress]) -> int:
        """Insert or replace one snapshot per trading day; return how many were written."""
        if not snapshots:
            return 0
        rows = [
            {
                "plan_id": plan_id,
                "trade_date": s.as_of,
                "close": s.last_close,
                "return_pct": s.return_pct,
                "progress_pct": s.progress_pct,
                "day_number": s.day_number,
                "total_days": s.total_days,
                "target_reached_on": s.target_reached_on,
                "stop_hit_on": s.stop_hit_on,
                "is_end_date_reached": s.is_end_date_reached,
            }
            for s in snapshots
        ]
        statement = insert(PlanDailyStatusModel).values(rows)
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=["plan_id", "trade_date"],
                set_={column: statement.excluded[column] for column in SNAPSHOT_COLUMNS},
            )
        )
        return len(snapshots)

    async def list_for_plan(self, plan_id: int) -> list[PlanProgress]:
        """Return the plan's snapshots in date order."""
        rows = await self._session.scalars(
            select(PlanDailyStatusModel)
            .where(PlanDailyStatusModel.plan_id == plan_id)
            .order_by(PlanDailyStatusModel.trade_date)
        )
        return [
            PlanProgress(
                as_of=r.trade_date,
                day_number=r.day_number,
                total_days=r.total_days,
                last_close=r.close,
                return_pct=r.return_pct,
                progress_pct=r.progress_pct,
                target_reached_on=r.target_reached_on,
                stop_hit_on=r.stop_hit_on,
                is_end_date_reached=r.is_end_date_reached,
            )
            for r in rows
        ]

    async def delete_all(self) -> int:
        """Delete every snapshot (rebuilt by ``make track``)."""
        result = await self._session.execute(delete(PlanDailyStatusModel))
        return int(result.rowcount or 0)  # type: ignore[attr-defined]


class SqlAlchemySettingsRepository:
    """``journal_settings``: one row per user; the row without a user predates accounts."""

    def __init__(self, session: AsyncSession) -> None:
        """Use ``session`` for every query."""
        self._session = session

    def _where(self, user_id: UUID | None) -> ColumnElement[bool]:
        column = JournalSettingsModel.user_id
        return column.is_(None) if user_id is None else column == user_id

    async def get(self, user_id: UUID | None = None) -> JournalSettings:
        """Return the user's settings, or the defaults when none are saved yet."""
        row = await self._session.scalar(select(JournalSettingsModel).where(self._where(user_id)))
        if row is None:
            return JournalSettings()
        return JournalSettings(
            paper_capital=row.paper_capital,
            risk_pct=row.risk_pct,
            success_tolerance_pp=row.success_tolerance_pp,
            default_stop_pct=row.default_stop_pct,
        )

    async def save(self, settings: JournalSettings, user_id: UUID | None = None) -> None:
        """Create or replace the user's settings."""
        values = {
            "paper_capital": settings.paper_capital,
            "risk_pct": settings.risk_pct,
            "success_tolerance_pp": settings.success_tolerance_pp,
            "default_stop_pct": settings.default_stop_pct,
        }
        row = await self._session.scalar(select(JournalSettingsModel).where(self._where(user_id)))
        if row is None:
            self._session.add(JournalSettingsModel(user_id=user_id, **values))
        else:
            for key, value in values.items():
                setattr(row, key, value)
            row.updated_at = func.now()
        await self._session.flush()

    async def claim_unowned(self, user_id: UUID) -> None:
        """Give the pre-accounts record to ``user_id`` unless they already have settings."""
        if await self._session.scalar(
            select(JournalSettingsModel.id).where(JournalSettingsModel.user_id == user_id)
        ):
            return
        await self._session.execute(
            update(JournalSettingsModel)
            .where(JournalSettingsModel.user_id.is_(None))
            .values(user_id=user_id)
        )
