"""Declarative base and naming conventions shared by every ORM model."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Constraint and index names follow docs/24-coding-standards.md, so Alembic
# autogenerate produces stable, readable names.
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models; its metadata is the migration target."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
