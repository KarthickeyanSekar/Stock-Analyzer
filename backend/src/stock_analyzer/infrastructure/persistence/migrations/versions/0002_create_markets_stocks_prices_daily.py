"""Create markets, stocks and the prices_daily hypertable.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRICE = sa.Numeric(18, 4)


def upgrade() -> None:
    """Create the tables and turn prices_daily into a TimescaleDB hypertable."""
    op.create_table(
        "markets",
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_markets")),
    )
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("market_code", sa.String(8), nullable=False),
        sa.Column("exchange", sa.String(16), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("source_provider", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["market_code"], ["markets.code"], name=op.f("fk_stocks_market_code_markets")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stocks")),
        sa.UniqueConstraint("exchange", "symbol", name=op.f("uq_stocks_exchange_symbol")),
    )
    op.create_index(op.f("ix_stocks_market_code"), "stocks", ["market_code"])
    op.create_table(
        "prices_daily",
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", PRICE, nullable=False),
        sa.Column("high", PRICE, nullable=False),
        sa.Column("low", PRICE, nullable=False),
        sa.Column("close", PRICE, nullable=False),
        sa.Column("adj_close", PRICE, nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("source_provider", sa.String(32), nullable=False),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stocks.id"], name=op.f("fk_prices_daily_stock_id_stocks")
        ),
        sa.PrimaryKeyConstraint("stock_id", "trade_date", name=op.f("pk_prices_daily")),
    )
    # Hand-written: autogenerate can't create hypertables. One chunk per year of trading days.
    op.execute(
        "SELECT create_hypertable('prices_daily', by_range('trade_date', INTERVAL '1 year'))"
    )


def downgrade() -> None:
    """Drop the tables (the hypertable's chunks are dropped with it)."""
    op.drop_table("prices_daily")
    op.drop_index(op.f("ix_stocks_market_code"), table_name="stocks")
    op.drop_table("stocks")
    op.drop_table("markets")
