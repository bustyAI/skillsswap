"""MessageThread model - container for messages within a mentorship.

Each Mentorship has exactly one MessageThread for communication.
Messages are scoped to the relationship - no open DMs.

Key behaviors:
- One-to-one with Mentorship (UNIQUE mentorship_id)
- Contains ordered Messages
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentorship import Mentorship
    from app.db.models.message import Message


class MessageThread(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A message thread for a mentorship relationship.

    Attributes:
        id: UUID primary key
        mentorship_id: FK to Mentorship (unique - one thread per mentorship)
        mentorship: The parent Mentorship
        messages: List of messages in this thread
    """

    __tablename__ = "message_thread"

    mentorship_id: Mapped[UUID] = mapped_column(
        ForeignKey("mentorship.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Relationships
    mentorship: Mapped[Mentorship] = relationship(
        "Mentorship",
        back_populates="message_thread",
    )

    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="thread",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<MessageThread mentorship={self.mentorship_id}>"
