"""Database module for SkillSwap.

This module provides:
- SQLAlchemy declarative base
- Soft-delete helpers
- Database session management
- FastAPI dependencies for database access
"""

from app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    apply_soft_delete_filter,
    soft_delete_select,
)
from app.db.dependencies import DbSession, get_db
from app.db.session import async_session_factory, engine

__all__ = [
    "Base",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "apply_soft_delete_filter",
    "soft_delete_select",
    "async_session_factory",
    "engine",
    # Dependencies
    "get_db",
    "DbSession",
]
