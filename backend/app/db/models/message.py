"""Message model - a single message within a message thread.

Messages are scoped to a MessageThread (which belongs to a Mentorship).
Only parties to the mentorship can send messages.

Key behaviors:
- Belongs to a MessageThread
- Has a sender (User)
- is_system flag for system-generated messages (e.g., "Mentorship started")
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.message_thread import MessageThread
    from app.db.models.user import User


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A message in a mentorship conversation.

    Attributes:
        id: UUID primary key
        thread_id: FK to MessageThread
        sender_id: FK to User who sent the message (NULL for system messages)
        content: The message text
        is_system: True for system-generated messages
        thread: The parent MessageThread
        sender: The User who sent this message
    """

    __tablename__ = "message"

    thread_id: Mapped[UUID] = mapped_column(
        ForeignKey("message_thread.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # sender_id can be NULL for system messages
    sender_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    thread: Mapped[MessageThread] = relationship(
        "MessageThread",
        back_populates="messages",
    )

    sender: Mapped[User | None] = relationship(
        "User",
        backref="messages_sent",
    )

    def __repr__(self) -> str:
        msg_type = "system" if self.is_system else f"user={self.sender_id}"
        return f"<Message {self.id} {msg_type}>"
