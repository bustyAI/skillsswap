"""Review model - a mentee's review of a completed meeting.

Reviews are left by mentees after meetings are completed.
They update the mentor's rating_avg and rating_count via a database trigger.

Key behaviors:
- One review per meeting (UNIQUE meeting_id)
- Rating must be 1-5 (CHECK constraint)
- editable_until: Reviews can only be edited within a time window
- Trigger updates mentor_profile aggregate ratings on INSERT/UPDATE
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.meeting import Meeting
    from app.db.models.user import User


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A review of a completed meeting.

    Attributes:
        id: UUID primary key
        meeting_id: FK to Meeting (unique - one review per meeting)
        reviewer_id: FK to User who wrote the review (the mentee)
        rating: 1-5 star rating
        comment: Optional text feedback
        editable_until: Deadline for editing the review
        meeting: The reviewed Meeting
        reviewer: The User who wrote this review
    """

    __tablename__ = "review"

    meeting_id: Mapped[UUID] = mapped_column(
        ForeignKey("meeting.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Reviews are editable for a limited time after creation
    # Set by application to created_at + 7 days
    editable_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    meeting: Mapped[Meeting] = relationship(
        "Meeting",
        back_populates="review",
    )

    reviewer: Mapped[User] = relationship(
        "User",
        backref="reviews_written",
    )

    __table_args__ = (
        # Rating must be between 1 and 5
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_review_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<Review meeting={self.meeting_id} rating={self.rating}>"
