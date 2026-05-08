"""Mentorship model - represents an ongoing mentor-mentee relationship.

A Mentorship is created when a mentee requests mentoring from a mentor.
It progresses through states: REQUESTED -> ACTIVE -> ENDED (or DECLINED).

Key behaviors:
- UNIQUE(mentor_id, mentee_id): Only one relationship per pair
- CHECK(mentor_id <> mentee_id): Cannot mentor yourself
- Owns a MessageThread for communication
- Has many Meetings for scheduled sessions
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.meeting import Meeting
    from app.db.models.message_thread import MessageThread
    from app.db.models.user import User


class MentorshipStatus(enum.StrEnum):
    """Status of a mentorship relationship."""

    REQUESTED = "REQUESTED"  # Mentee has requested, awaiting mentor response
    ACTIVE = "ACTIVE"  # Mentor accepted, relationship is active
    ENDED = "ENDED"  # Either party ended the relationship
    DECLINED = "DECLINED"  # Mentor declined the request


class Mentorship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A mentorship relationship between two users.

    Attributes:
        id: UUID primary key
        mentor_id: FK to User who is the mentor
        mentee_id: FK to User who is the mentee
        status: Current state of the relationship
        message_thread: One-to-one relationship to MessageThread
        meetings: List of meetings in this mentorship
        mentor: The mentor User
        mentee: The mentee User
    """

    __tablename__ = "mentorship"

    mentor_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mentee_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[MentorshipStatus] = mapped_column(
        Enum(MentorshipStatus, name="mentorship_status"),
        nullable=False,
        default=MentorshipStatus.REQUESTED,
    )

    # Relationships
    mentor: Mapped[User] = relationship(
        "User",
        foreign_keys=[mentor_id],
        backref="mentorships_as_mentor",
    )

    mentee: Mapped[User] = relationship(
        "User",
        foreign_keys=[mentee_id],
        backref="mentorships_as_mentee",
    )

    message_thread: Mapped[MessageThread | None] = relationship(
        "MessageThread",
        back_populates="mentorship",
        uselist=False,
    )

    meetings: Mapped[list[Meeting]] = relationship(
        "Meeting",
        back_populates="mentorship",
    )

    __table_args__ = (
        # Only one mentorship relationship per mentor-mentee pair
        UniqueConstraint(
            "mentor_id",
            "mentee_id",
            name="uq_mentorship_mentor_mentee",
        ),
        # Cannot mentor yourself
        CheckConstraint(
            "mentor_id <> mentee_id",
            name="ck_mentorship_no_self_mentorship",
        ),
    )

    def __repr__(self) -> str:
        return f"<Mentorship mentor={self.mentor_id} mentee={self.mentee_id} status={self.status.value}>"
