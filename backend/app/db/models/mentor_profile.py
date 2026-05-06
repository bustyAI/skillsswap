"""MentorProfile model - extends a User to be a mentor.

A MentorProfile is created when a user opts to become a mentor.
Each user can have at most one mentor profile (enforced by UNIQUE on user_id).

Key behaviors:
- One-to-one with User: The user_id FK is unique
- is_enabled: Admins can disable mentors without deleting them
- rating_avg/rating_count: Computed from reviews via database trigger
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentor_embedding import MentorEmbedding
    from app.db.models.mentor_topic import MentorTopic
    from app.db.models.user import User


class MentorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A mentor profile extending a User.

    Attributes:
        id: UUID primary key (from UUIDPrimaryKeyMixin)
        user_id: FK to User - the user who is this mentor
        bio: Longer description of mentor's background (markdown OK)
        headline: Short tagline shown in search results
        is_enabled: Whether the mentor is active (admin can disable)
        rating_avg: Average rating from reviews (computed by trigger)
        rating_count: Number of reviews received (computed by trigger)
        last_active_at: Last time mentor took an action (for ranking)
        created_at: When profile was created (from TimestampMixin)
        updated_at: Last modification time (from TimestampMixin)
        user: Back-reference to the User
    """

    __tablename__ = "mentor_profile"

    # Foreign key to User - UNIQUE ensures one-to-one relationship
    # ON DELETE CASCADE: if user is hard-deleted, profile goes too
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Bio - longer text description, can contain multiple paragraphs
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Headline - short tagline for search results (e.g., "Senior Python Developer")
    headline: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # Is this mentor currently enabled? Admins can disable without deleting
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Rating aggregate - computed by database trigger when reviews change
    # NUMERIC(3,2) stores values like 4.75 with 2 decimal places
    rating_avg: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    # Count of reviews - used for "rating confidence" in recommendations
    rating_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Last activity timestamp - used in recommendation ranking
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Back-reference to User
    user: Mapped[User] = relationship(
        "User",
        back_populates="mentor_profile",
    )

    # Relationship to MentorTopic join table
    mentor_topics: Mapped[list[MentorTopic]] = relationship(
        "MentorTopic",
        back_populates="mentor_profile",
    )

    # One-to-one relationship to embedding
    embedding: Mapped[MentorEmbedding | None] = relationship(
        "MentorEmbedding",
        back_populates="mentor_profile",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<MentorProfile user_id={self.user_id} enabled={self.is_enabled}>"
