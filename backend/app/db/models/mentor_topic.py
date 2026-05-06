"""MentorTopic model - join table linking mentors to their topics.

"Skills are modeled via the MentorTopic join table. Never as a skills: string[] column."

This allows:
- Many-to-many relationship between mentors and topics
- Querying mentors by topic efficiently
- Adding metadata to the relationship in the future (e.g., years of experience)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentor_profile import MentorProfile
    from app.db.models.topic import Topic


class MentorTopic(Base, UUIDPrimaryKeyMixin):
    """Join table linking a MentorProfile to a Topic.

    Attributes:
        id: UUID primary key
        mentor_profile_id: FK to mentor_profile
        topic_id: FK to topic
        mentor_profile: Relationship to MentorProfile
        topic: Relationship to Topic
    """

    __tablename__ = "mentor_topic"

    mentor_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("mentor_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic_id: Mapped[UUID] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    mentor_profile: Mapped[MentorProfile] = relationship(
        "MentorProfile",
        back_populates="mentor_topics",
    )

    topic: Mapped[Topic] = relationship(
        "Topic",
        back_populates="mentor_topics",
    )

    __table_args__ = (
        # Each mentor can only have a topic once
        UniqueConstraint(
            "mentor_profile_id",
            "topic_id",
            name="uq_mentor_topic_mentor_profile_id_topic_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<MentorTopic mentor={self.mentor_profile_id} topic={self.topic_id}>"
