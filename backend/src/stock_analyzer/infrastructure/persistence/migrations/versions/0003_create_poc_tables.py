"""Create the remaining Phase 1 POC tables.

fundamentals, corporate_actions, model_versions, predictions, trade_plans,
plan_daily_status, providers, provider_credentials, provider_assignments, job_runs.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-31

Reviewed: no hypertables, pgvector indexes or extensions are needed in this revision.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("job_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_processed", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'SUCCEEDED', 'FAILED')", name=op.f("ck_job_runs_status")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_runs")),
    )
    op.create_index(
        op.f("ix_job_runs_job_name_started_at"),
        "job_runs",
        ["job_name", "started_at"],
        unique=False,
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=4), nullable=True),
        sa.Column("algorithm", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "params", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column(
            "metrics", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column(
            "trained_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('CANDIDATE', 'ACTIVE', 'RETIRED')", name=op.f("ck_model_versions_status")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_versions")),
        sa.UniqueConstraint("name", "category", name=op.f("uq_model_versions_name_category")),
    )
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("plugin_name", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "settings", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('MARKET_DATA', 'FUNDAMENTALS', 'MACRO', 'NOTIFY', 'LLM')",
            name=op.f("ck_providers_kind"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_providers")),
        sa.UniqueConstraint("plugin_name", name=op.f("uq_providers_plugin_name")),
    )
    op.create_table(
        "provider_assignments",
        sa.Column("market_code", sa.String(length=8), nullable=False),
        sa.Column("data_type", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("priority >= 1", name=op.f("ck_provider_assignments_priority_positive")),
        sa.ForeignKeyConstraint(
            ["market_code"],
            ["markets.code"],
            name=op.f("fk_provider_assignments_market_code_markets"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["providers.id"],
            name=op.f("fk_provider_assignments_provider_id_providers"),
        ),
        sa.PrimaryKeyConstraint(
            "market_code", "data_type", "priority", name=op.f("pk_provider_assignments")
        ),
        sa.UniqueConstraint(
            "market_code",
            "data_type",
            "provider_id",
            name=op.f("uq_provider_assignments_market_code_data_type_provider_id"),
        ),
    )
    op.create_table(
        "provider_credentials",
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column("value_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["providers.id"],
            name=op.f("fk_provider_credentials_provider_id_providers"),
        ),
        sa.PrimaryKeyConstraint("provider_id", "field", name=op.f("pk_provider_credentials")),
    )
    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("action_type", sa.String(length=16), nullable=False),
        sa.Column("ratio_from", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("ratio_to", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("source_provider", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "action_type IN ('SPLIT', 'BONUS', 'DIVIDEND')",
            name=op.f("ck_corporate_actions_action_type"),
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stocks.id"], name=op.f("fk_corporate_actions_stock_id_stocks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_corporate_actions")),
        sa.UniqueConstraint(
            "stock_id",
            "ex_date",
            "action_type",
            name=op.f("uq_corporate_actions_stock_id_ex_date_action_type"),
        ),
    )
    op.create_index(
        op.f("ix_corporate_actions_stock_id"), "corporate_actions", ["stock_id"], unique=False
    )
    op.create_table(
        "fundamentals",
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("period_type", sa.String(length=2), nullable=False),
        sa.Column("announced_date", sa.Date(), nullable=True),
        sa.Column("statements", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ratios", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_provider", sa.String(length=32), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("period_type IN ('Q', 'FY')", name=op.f("ck_fundamentals_period_type")),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stocks.id"], name=op.f("fk_fundamentals_stock_id_stocks")
        ),
        sa.PrimaryKeyConstraint(
            "stock_id", "period_end", "period_type", name=op.f("pk_fundamentals")
        ),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=4), nullable=False),
        sa.Column("p10_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column("p50_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column("p90_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column("prob_up", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("prob_hit", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('50D', '100D', '200D', '300D', '1Y', '2Y', '3Y', '5Y')",
            name=op.f("ck_predictions_category"),
        ),
        sa.CheckConstraint(
            "p10_pct <= p50_pct AND p50_pct <= p90_pct",
            name=op.f("ck_predictions_ordered_quantiles"),
        ),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_predictions_model_version_id_model_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stocks.id"], name=op.f("fk_predictions_stock_id_stocks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
        sa.UniqueConstraint(
            "stock_id",
            "as_of",
            "category",
            "model_version_id",
            name=op.f("uq_predictions_stock_id_as_of_category_model_version_id"),
        ),
    )
    op.create_index(
        op.f("ix_predictions_stock_id_as_of"), "predictions", ["stock_id", "as_of"], unique=False
    )
    op.create_table(
        "trade_plans",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.BigInteger(), nullable=True),
        sa.Column("parent_plan_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(length=4), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("planned_end_date", sa.Date(), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("target_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column("stop_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column(
            "success_tolerance_pp",
            sa.Numeric(precision=5, scale=2),
            server_default="0.5",
            nullable=False,
        ),
        sa.Column("trailing_stop_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(length=8), server_default="ACTIVE", nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=True),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("exit_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("actual_return_pct", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'ACTIVE' AND outcome IS NULL AND exit_date IS NULL AND exit_price IS NULL) OR (status = 'CLOSED' AND outcome IS NOT NULL AND exit_date IS NOT NULL AND exit_price IS NOT NULL)",
            name=op.f("ck_trade_plans_closed_has_exit"),
        ),
        sa.CheckConstraint(
            "category IN ('50D', '100D', '200D', '300D', '1Y', '2Y', '3Y', '5Y')",
            name=op.f("ck_trade_plans_category"),
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('SUCCESS', 'PARTIAL', 'FAILURE', 'EXITED_EARLY')",
            name=op.f("ck_trade_plans_outcome"),
        ),
        sa.CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name=op.f("ck_trade_plans_status")),
        sa.CheckConstraint(
            "exit_date IS NULL OR exit_date >= start_date",
            name=op.f("ck_trade_plans_exit_after_start"),
        ),
        sa.CheckConstraint(
            "success_tolerance_pp >= 0", name=op.f("ck_trade_plans_tolerance_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["parent_plan_id"],
            ["trade_plans.id"],
            name=op.f("fk_trade_plans_parent_plan_id_trade_plans"),
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"],
            ["predictions.id"],
            name=op.f("fk_trade_plans_prediction_id_predictions"),
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stocks.id"], name=op.f("fk_trade_plans_stock_id_stocks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trade_plans")),
    )
    op.create_index(op.f("ix_trade_plans_stock_id"), "trade_plans", ["stock_id"], unique=False)
    op.create_table(
        "plan_daily_status",
        sa.Column("plan_id", sa.BigInteger(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("return_pct", sa.Numeric(precision=9, scale=4), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("is_target_reached", sa.Boolean(), nullable=False),
        sa.Column("is_stop_hit", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["trade_plans.id"], name=op.f("fk_plan_daily_status_plan_id_trade_plans")
        ),
        sa.PrimaryKeyConstraint("plan_id", "trade_date", name=op.f("pk_plan_daily_status")),
    )


def downgrade() -> None:
    """Revert this migration."""
    op.drop_table("plan_daily_status")
    op.drop_index(op.f("ix_trade_plans_stock_id"), table_name="trade_plans")
    op.drop_table("trade_plans")
    op.drop_index(op.f("ix_predictions_stock_id_as_of"), table_name="predictions")
    op.drop_table("predictions")
    op.drop_table("fundamentals")
    op.drop_index(op.f("ix_corporate_actions_stock_id"), table_name="corporate_actions")
    op.drop_table("corporate_actions")
    op.drop_table("provider_credentials")
    op.drop_table("provider_assignments")
    op.drop_table("providers")
    op.drop_table("model_versions")
    op.drop_index(op.f("ix_job_runs_job_name_started_at"), table_name="job_runs")
    op.drop_table("job_runs")
