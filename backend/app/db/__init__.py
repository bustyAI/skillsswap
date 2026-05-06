"""Database module for SkillSwap.

This module provides:
- SQLAlchemy declarative base
- Soft-delete helpers
- Database session management
"""

from app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    apply_soft_delete_filter,
    soft_delete_select,
)
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
]
