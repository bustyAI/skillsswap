"""TopicEmbedding model - stores vector embedding for topics.

- Rule #6: "Embedding dimension is 384." (from all-MiniLM-L6-v2 model)
- Rule #7: "Two separate embedding tables." (mentor_embedding and topic_embedding)

The embedding is generated from the topic's name + description and used
as the query vector for finding relevant mentors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.topic import Topic

from pgvector.sqlalchemy import Vector


class TopicEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector embedding for a topic.

    Attributes:
        id: UUID primary key
        topic_id: FK to topic (unique - one embedding per topic)
        embedding: 384-dimensional vector from sentence-transformers
        topic: Relationship to Topic
    """

    __tablename__ = "topic_embedding"

    topic_id: Mapped[UUID] = mapped_column(
        ForeignKey("topic.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 384-dim vector from all-MiniLM-L6-v2
    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    # Relationship back to topic
    topic: Mapped[Topic] = relationship(
        "Topic",
        back_populates="embedding",
    )

    def __repr__(self) -> str:
        return f"<TopicEmbedding topic_id={self.topic_id}>"
