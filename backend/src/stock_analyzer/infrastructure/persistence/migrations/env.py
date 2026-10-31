"""Alembic environment: runs migrations with the async engine from ``SA_DATABASE_URL``."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from stock_analyzer.infrastructure.config.settings import get_settings
from stock_analyzer.infrastructure.persistence.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tables owned by extensions (TimescaleDB, pgvector) are never touched by autogenerate.
EXTENSION_SCHEMAS = {"_timescaledb_catalog", "_timescaledb_config", "_timescaledb_internal"}


def include_object(
    obj: object, name: str | None, type_: str, reflected: bool, compare_to: object
) -> bool:
    """Skip objects that exist in the database but are not ORM models (e.g., extension tables)."""
    schema = getattr(obj, "schema", None)
    if schema in EXTENSION_SCHEMAS:
        return False
    # TimescaleDB adds `<table>_<column>_idx` when creating a hypertable; our own indexes use `ix_`.
    if type_ == "index" and reflected and compare_to is None and (name or "").endswith("_idx"):
        return False
    return not (type_ == "table" and reflected and compare_to is None)


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a database connection (``alembic upgrade --sql``)."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against the database using the async driver."""
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
