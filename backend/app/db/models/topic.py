"""Topic model - represents a skill or subject area for mentorship.

Topics form a hierarchy via parent_topic_id. For example:
- Programming (parent)
  - Python (child)
  - JavaScript (child)

Key behaviors:
- Self-referential FK for hierarchy (nullable parent_topic_id)
- Unique name constraint
- No soft-delete (admin-managed reference data)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentor_topic import MentorTopic
    from app.db.models.topic_embedding import TopicEmbedding


class Topic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A skill or subject area available for mentorship.

    Attributes:
        id: UUID primary key
        name: Display name (unique)
        description: Longer explanation of the topic
        parent_topic_id: Optional FK to parent topic for hierarchy
        parent: Relationship to parent Topic
        children: Relationship to child Topics
        mentor_topics: Join table entries linking mentors to this topic
        embedding: One-to-one relationship to TopicEmbedding
    """

    __tablename__ = "topic"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Self-referential FK for topic hierarchy
    parent_topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topic.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Self-referential relationships
    parent: Mapped[Topic | None] = relationship(
        "Topic",
        remote_side="Topic.id",
        back_populates="children",
    )

    children: Mapped[list[Topic]] = relationship(
        "Topic",
        back_populates="parent",
    )

    # Relationship to MentorTopic join table
    mentor_topics: Mapped[list[MentorTopic]] = relationship(
        "MentorTopic",
        back_populates="topic",
    )

    # One-to-one relationship to embedding
    embedding: Mapped[TopicEmbedding | None] = relationship(
        "TopicEmbedding",
        back_populates="topic",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Topic {self.name!r} ({self.id})>"
