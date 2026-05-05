"""SQLAlchemy declarative base and soft-delete helpers.

This module provides the foundation for all database models:
- Base: The declarative base class all models inherit from
- SoftDeleteMixin: Mixin for models that support soft-delete
- apply_soft_delete_filter: Helper to filter out soft-deleted rows

Per architectural rule #3 from CLAUDE.md:
"All queries filter deleted_at IS NULL by default."
"""

from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import DateTime, Select, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar("T")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models inherit from this class. It provides:
    - Type annotation support via DeclarativeBase
    - Common metadata configuration
    """

    pass


class TimestampMixin:
    """Mixin providing created_at and updated_at columns.

    The updated_at column is automatically set via a database trigger
    (created in the base migration). Do not set it manually.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for models that support soft-delete.

    Models with this mixin are never hard-deleted. Instead, deleted_at
    is set to the current timestamp. All queries should filter out rows
    where deleted_at IS NOT NULL using apply_soft_delete_filter().

    Per architectural rule #2 from CLAUDE.md:
    "Soft-delete-with-cascade for users."
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        index=True,
    )


class UUIDPrimaryKeyMixin:
    """Mixin providing a UUID primary key.

    Per architectural rule #1 from CLAUDE.md:
    "UUIDs everywhere. Every primary key and foreign key is UUID v4."

    Uses PostgreSQL's gen_random_uuid() for server-side generation.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


def apply_soft_delete_filter[T](stmt: Select[tuple[T]], model: Any) -> Select[tuple[T]]:
    """Apply soft-delete filter to a SELECT statement.

    Adds WHERE deleted_at IS NULL to exclude soft-deleted rows.

    Args:
        stmt: A SQLAlchemy Select statement
        model: The model class with deleted_at column

    Returns:
        The statement with the soft-delete filter applied

    Example:
        stmt = select(User).where(User.email == email)
        stmt = apply_soft_delete_filter(stmt, User)
        result = await session.execute(stmt)

    Note:
        Admin-only queries that need to see deleted rows should NOT
        call this function. This opt-in approach is per CLAUDE.md rule #3.
    """
    return stmt.where(model.deleted_at.is_(None))


def soft_delete_select[T](model: type[T]) -> Select[tuple[T]]:
    """Create a SELECT statement with soft-delete filter pre-applied.

    Convenience function that combines select() with apply_soft_delete_filter().

    Args:
        model: The model class to select from

    Returns:
        A Select statement filtering out soft-deleted rows

    Example:
        stmt = soft_delete_select(User).where(User.email == email)
        result = await session.execute(stmt)
    """
    stmt = select(model)
    return apply_soft_delete_filter(stmt, model)
