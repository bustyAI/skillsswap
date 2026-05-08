"""Meeting model - represents a scheduled session within a mentorship.

A Meeting is a single scheduled event between mentor and mentee.
It progresses through states: REQUESTED -> SCHEDULED -> COMPLETED (or CANCELLED).

Key behaviors:
- Belongs to a Mentorship
- CHECK: SCHEDULED status requires scheduled_time AND meeting_url
- Has one optional Review (from mentee after completion)
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentorship import Mentorship
    from app.db.models.review import Review


class MeetingStatus(enum.StrEnum):
    """Status of a meeting."""

    REQUESTED = "REQUESTED"  # Mentee requested, awaiting scheduling
    SCHEDULED = "SCHEDULED"  # Mentor provided time and URL
    COMPLETED = "COMPLETED"  # Meeting took place
    CANCELLED = "CANCELLED"  # Meeting was cancelled


class Meeting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A scheduled meeting within a mentorship.

    Attributes:
        id: UUID primary key
        mentorship_id: FK to the parent Mentorship
        scheduled_time: When the meeting is scheduled (required for SCHEDULED)
        meeting_url: URL for video call (required for SCHEDULED)
        status: Current state of the meeting
        mentorship: The parent Mentorship
        review: Optional review from mentee after completion
    """

    __tablename__ = "meeting"

    mentorship_id: Mapped[UUID] = mapped_column(
        ForeignKey("mentorship.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Meeting URL - validated in application layer against allowed domains
    meeting_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, name="meeting_status"),
        nullable=False,
        default=MeetingStatus.REQUESTED,
    )

    # Relationships
    mentorship: Mapped[Mentorship] = relationship(
        "Mentorship",
        back_populates="meetings",
    )

    review: Mapped[Review | None] = relationship(
        "Review",
        back_populates="meeting",
        uselist=False,
    )

    __table_args__ = (
        # If status is SCHEDULED, both scheduled_time and meeting_url must be set
        CheckConstraint(
            "(status != 'SCHEDULED') OR (scheduled_time IS NOT NULL AND meeting_url IS NOT NULL)",
            name="ck_meeting_scheduled_requires_time_and_url",
        ),
    )

    def __repr__(self) -> str:
        return f"<Meeting {self.id} status={self.status.value}>"
