"""Create the PostgreSQL extensions the app depends on.

Revision ID: 0001
Revises:
Create Date: 2026-10-31

TimescaleDB needs the full (not -oss) image; see docs/25-infrastructure-services-inventory.md.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXTENSIONS = ("timescaledb", "vector", "pgcrypto")


def upgrade() -> None:
    """Create the extensions if they are not already installed."""
    for extension in EXTENSIONS:
        op.execute(f"CREATE EXTENSION IF NOT EXISTS {extension}")


def downgrade() -> None:
    """Drop the extensions (dev/test only: this removes every hypertable)."""
    for extension in reversed(EXTENSIONS):
        op.execute(f"DROP EXTENSION IF EXISTS {extension}")
