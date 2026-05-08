"""Report model - represents a user-submitted report for moderation.

A Report is filed when a user wants to flag inappropriate behavior,
content, or another user for admin review.

Key behaviors:
- Status transitions: PENDING -> UNDER_REVIEW -> RESOLVED/DISMISSED
- Can target a user, a mentorship, or both
- Resolution tracked with notes, admin, and timestamp
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentorship import Mentorship
    from app.db.models.user import User


class ReportStatus(enum.StrEnum):
    """Status of a report in the moderation queue."""

    PENDING = "PENDING"  # Newly submitted, awaiting review
    UNDER_REVIEW = "UNDER_REVIEW"  # Admin is investigating
    RESOLVED = "RESOLVED"  # Action taken, report closed
    DISMISSED = "DISMISSED"  # No action needed, report closed


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user-submitted report for moderation review.

    Attributes:
        id: UUID primary key
        reporter_id: FK to User who filed the report
        reported_user_id: FK to User being reported (optional)
        reported_mentorship_id: FK to Mentorship being reported (optional)
        reason: Description of why the report was filed
        status: Current state in the moderation workflow
        resolution_notes: Admin notes on how it was resolved (optional)
        resolved_by_id: FK to admin User who resolved (optional)
        resolved_at: When the report was resolved (optional)
        reporter: The User who filed the report
        reported_user: The User being reported (if applicable)
        reported_mentorship: The Mentorship being reported (if applicable)
        resolved_by: The admin User who resolved (if applicable)
    """

    __tablename__ = "report"

    # Who filed the report
    reporter_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What/who is being reported (at least one should be set at application layer)
    reported_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    reported_mentorship_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("mentorship.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Report content
    reason: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )

    # Status tracking
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"),
        nullable=False,
        default=ReportStatus.PENDING,
    )

    # Resolution details (populated when resolved/dismissed)
    resolution_notes: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    resolved_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    reporter: Mapped[User] = relationship(
        "User",
        foreign_keys=[reporter_id],
        backref="reports_filed",
    )

    reported_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[reported_user_id],
        backref="reports_against",
    )

    reported_mentorship: Mapped[Mentorship | None] = relationship(
        "Mentorship",
        foreign_keys=[reported_mentorship_id],
        backref="reports",
    )

    resolved_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[resolved_by_id],
        backref="reports_resolved",
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} status={self.status.value}>"
