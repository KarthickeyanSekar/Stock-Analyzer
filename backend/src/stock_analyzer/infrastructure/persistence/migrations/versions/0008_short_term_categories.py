"""Short-term holding periods 1D, 3D, 5D, 10D (Phase 7, Q75): widen the category checks.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-01 18:00:00+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LONG = "('50D', '100D', '200D', '300D', '1Y', '2Y', '3Y', '5Y')"
WITH_SHORT = "('1D', '3D', '5D', '10D', '50D', '100D', '200D', '300D', '1Y', '2Y', '3Y', '5Y')"
TABLES = ("predictions", "trade_plans", "labels_daily")


def _replace_checks(allowed: str) -> None:
    for table in TABLES:
        name = op.f(f"ck_{table}_category")
        op.drop_constraint(name, table, type_="check")
        op.create_check_constraint(name, table, f"category IN {allowed}")


def upgrade() -> None:
    """Allow the short-term categories."""
    _replace_checks(WITH_SHORT)


def downgrade() -> None:
    """Remove short-term rows, then restore the long-term-only checks."""
    for table in TABLES:
        if table == "trade_plans":
            op.execute(
                "DELETE FROM plan_daily_status WHERE plan_id IN "
                "(SELECT id FROM trade_plans WHERE category IN ('1D', '3D', '5D', '10D'))"
            )
        op.execute(f"DELETE FROM {table} WHERE category IN ('1D', '3D', '5D', '10D')")  # noqa: S608
    _replace_checks(LONG)
