"""Block model - represents a user blocking another user.

When a user blocks another, they will not see each other in recommendations,
cannot message each other, and cannot form new mentorships.

Key behaviors:
- UNIQUE(blocker_id, blocked_id): Only one block record per pair
- CHECK(blocker_id <> blocked_id): Cannot block yourself
- No updated_at: Blocks are created or deleted, never modified
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Block(Base, UUIDPrimaryKeyMixin):
    """A block relationship between two users.

    Note: This model intentionally has no updated_at column.
    Blocks are binary - they exist or they don't. There's no
    state to update, only create or delete.

    Attributes:
        id: UUID primary key
        blocker_id: FK to User who initiated the block
        blocked_id: FK to User who is blocked
        created_at: When the block was created
        blocker: The User who initiated the block
        blocked: The User who is blocked
    """

    __tablename__ = "block"

    blocker_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    blocked_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    blocker: Mapped[User] = relationship(
        "User",
        foreign_keys=[blocker_id],
        backref="blocks_created",
    )

    blocked: Mapped[User] = relationship(
        "User",
        foreign_keys=[blocked_id],
        backref="blocked_by",
    )

    __table_args__ = (
        # Only one block record per blocker-blocked pair
        UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_block_blocker_blocked",
        ),
        # Cannot block yourself
        CheckConstraint(
            "blocker_id <> blocked_id",
            name="ck_block_no_self_block",
        ),
    )

    def __repr__(self) -> str:
        return f"<Block {self.blocker_id} -> {self.blocked_id}>"
