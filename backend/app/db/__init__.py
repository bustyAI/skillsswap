"""Database module for SkillSwap.

This module provides:
- SQLAlchemy declarative base
- Soft-delete helpers
- Database session management (to be added)
"""

from app.db.base import Base, SoftDeleteMixin, apply_soft_delete_filter

__all__ = ["Base", "SoftDeleteMixin", "apply_soft_delete_filter"]
