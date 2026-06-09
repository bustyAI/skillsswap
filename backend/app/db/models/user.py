"""User model - represents authenticated users in the system.

A User is created via just-in-time provisioning when someone first
authenticates with Cognito. The cognito_sub links to their Cognito identity.

Key behaviors:
- Soft-delete: Users are never hard-deleted. deleted_at is set instead.
- Email uniqueness: Enforced only for active users (deleted_at IS NULL).
- One-to-one with MentorProfile: A user may optionally become a mentor.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

# TYPE_CHECKING is True only during type checking (mypy), not at runtime.
# This avoids import issues while still getting type hints.
if TYPE_CHECKING:
    from app.db.models.mentor_profile import MentorProfile


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """A registered user of SkillSwap.

    Attributes:
        id: UUID primary key (from UUIDPrimaryKeyMixin)
        cognito_sub: The 'sub' claim from the Cognito JWT - unique identifier
        email: User's email address (unique among active users)
        display_name: Optional display name shown in the UI
        avatar_url: Optional URL to profile picture (S3 or external)
        created_at: When the user was created (from TimestampMixin)
        updated_at: Last modification time (from TimestampMixin)
        deleted_at: Soft-delete timestamp (from SoftDeleteMixin)
        mentor_profile: Optional one-to-one relationship to MentorProfile
    """

    __tablename__ = "user"

    # Cognito subject ID - the unique identifier from AWS Cognito
    # This links our User to their Cognito identity
    cognito_sub: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Email - unique among ACTIVE users only (see __table_args__ below)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Display name shown in UI (optional - can use email if not set)
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Profile picture URL (optional)
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Admin moderation: when the user was banned (separate from soft-delete)
    banned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationship to MentorProfile (one-to-one, optional)
    # uselist=False means this returns a single object, not a list
    # back_populates creates the reverse relationship on MentorProfile
    mentor_profile: Mapped[MentorProfile | None] = relationship(
        "MentorProfile",
        back_populates="user",
        uselist=False,
    )

    # Table-level constraints and indexes
    __table_args__ = (
        # Partial unique index: email must be unique, but ONLY for active users
        # This allows a soft-deleted user's email to be reused by a new account
        Index(
            "ix_user_email_active",
            "email",
            unique=True,
            postgresql_where=(SoftDeleteMixin.deleted_at.is_(None)),
        ),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.id})>"
