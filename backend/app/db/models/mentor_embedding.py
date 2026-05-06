"""MentorEmbedding model - stores vector embedding for mentor profiles.

- Rule #6: "Embedding dimension is 384." (from all-MiniLM-L6-v2 model)
- Rule #7: "Two separate embedding tables." (mentor_embedding and topic_embedding)

The embedding is generated from the mentor's bio + topic names and used
for vector similarity search in recommendations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.mentor_profile import MentorProfile

from pgvector.sqlalchemy import Vector


class MentorEmbedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector embedding for a mentor profile.

    Attributes:
        id: UUID primary key
        mentor_profile_id: FK to mentor_profile (unique - one embedding per mentor)
        embedding: 384-dimensional vector from sentence-transformers
        mentor_profile: Relationship to MentorProfile
    """

    __tablename__ = "mentor_embedding"

    mentor_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("mentor_profile.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 384-dim vector from all-MiniLM-L6-v2
    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    # Relationship back to mentor profile
    mentor_profile: Mapped[MentorProfile] = relationship(
        "MentorProfile",
        back_populates="embedding",
    )

    def __repr__(self) -> str:
        return f"<MentorEmbedding mentor_profile_id={self.mentor_profile_id}>"
