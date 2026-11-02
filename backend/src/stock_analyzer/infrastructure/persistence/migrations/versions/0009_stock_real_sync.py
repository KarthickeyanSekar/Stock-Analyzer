"""Per-stock real-data sync flag (Admin > Data sources, max five stocks).

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-02 12:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``stocks.is_real_sync_enabled``."""
    op.add_column(
        "stocks",
        sa.Column("is_real_sync_enabled", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    """Drop the flag."""
    op.drop_column("stocks", "is_real_sync_enabled")
