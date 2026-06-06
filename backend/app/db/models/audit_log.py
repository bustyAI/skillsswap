"""AuditLog model - append-only record of admin actions.

Every admin action (bans, mentor disables, report resolutions, account deletions)
must be logged here. This table is append-only: no updates or deletes in
application code.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class AuditAction(enum.StrEnum):
    """Types of auditable admin actions."""

    BAN_USER = "BAN_USER"
    UNBAN_USER = "UNBAN_USER"
    DISABLE_MENTOR = "DISABLE_MENTOR"
    ENABLE_MENTOR = "ENABLE_MENTOR"
    RESOLVE_REPORT = "RESOLVE_REPORT"
    DISMISS_REPORT = "DISMISS_REPORT"
    DELETE_USER = "DELETE_USER"


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Append-only log of admin actions.

    Attributes:
        id: UUID primary key
        admin_id: FK to the admin User who performed the action
        action: The type of action taken
        target_user_id: FK to User who was acted upon (optional)
        target_report_id: UUID of the report acted upon (optional)
        details: Free-form notes about the action
        created_at: When the action was performed
    """

    __tablename__ = "audit_log"

    admin_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"),
        nullable=False,
        index=True,
    )

    target_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_report_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    admin: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[admin_id],
    )

    target_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[target_user_id],
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} by {self.admin_id} at {self.created_at}>"
