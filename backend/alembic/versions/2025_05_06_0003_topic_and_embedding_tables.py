"""Topic taxonomy and embedding tables.

Revision ID: 0003
Revises: 0002
Create Date: 2025-05-06

Creates tables for the topic taxonomy and vector embeddings:
- topic: Skill/subject areas with optional hierarchy
- mentor_topic: Join table linking mentors to topics
- mentor_embedding: 384-dim vector embeddings for mentor profiles
- topic_embedding: 384-dim vector embeddings for topics

Key constraints:
- topic.name is globally unique
- mentor_topic has unique(mentor_profile_id, topic_id)
- Embedding tables have unique FK (one embedding per entity)
- HNSW indexes on embedding columns for fast similarity search
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # === TOPIC TABLE ===
    op.create_table(
        "topic",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # Topic name - unique across all topics
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        # Description - longer explanation of the topic
        sa.Column("description", sa.Text(), nullable=True),
        # Self-referential FK for hierarchy (nullable = top-level topic)
        sa.Column(
            "parent_topic_id",
            sa.UUID(),
            sa.ForeignKey("topic.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index on parent_topic_id for hierarchy queries
    op.create_index("ix_topic_parent_topic_id", "topic", ["parent_topic_id"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_topic_updated_at
        BEFORE UPDATE ON topic
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === MENTOR_TOPIC JOIN TABLE ===
    op.create_table(
        "mentor_topic",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to mentor_profile - CASCADE on delete
        sa.Column(
            "mentor_profile_id",
            sa.UUID(),
            sa.ForeignKey("mentor_profile.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # FK to topic - CASCADE on delete
        sa.Column(
            "topic_id",
            sa.UUID(),
            sa.ForeignKey("topic.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Unique constraint: each mentor can only have a topic once
        sa.UniqueConstraint(
            "mentor_profile_id",
            "topic_id",
            name="uq_mentor_topic_mentor_profile_id_topic_id",
        ),
    )

    # Indexes for fast lookups
    op.create_index(
        "ix_mentor_topic_mentor_profile_id", "mentor_topic", ["mentor_profile_id"]
    )
    op.create_index("ix_mentor_topic_topic_id", "mentor_topic", ["topic_id"])

    # === MENTOR_EMBEDDING TABLE ===
    op.create_table(
        "mentor_embedding",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to mentor_profile - UNIQUE (one embedding per mentor)
        sa.Column(
            "mentor_profile_id",
            sa.UUID(),
            sa.ForeignKey("mentor_profile.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # 384-dimensional vector from all-MiniLM-L6-v2
        sa.Column(
            "embedding",
            Vector(384),
            nullable=False,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index on mentor_profile_id for fast lookups
    op.create_index(
        "ix_mentor_embedding_mentor_profile_id",
        "mentor_embedding",
        ["mentor_profile_id"],
    )

    # HNSW index for fast cosine similarity search
    # Using default parameters (m=16, ef_construction=64)
    op.execute(
        """
        CREATE INDEX ix_mentor_embedding_embedding_hnsw
        ON mentor_embedding
        USING hnsw (embedding vector_cosine_ops)
        """
    )

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_mentor_embedding_updated_at
        BEFORE UPDATE ON mentor_embedding
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === TOPIC_EMBEDDING TABLE ===
    op.create_table(
        "topic_embedding",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to topic - UNIQUE (one embedding per topic)
        sa.Column(
            "topic_id",
            sa.UUID(),
            sa.ForeignKey("topic.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # 384-dimensional vector from all-MiniLM-L6-v2
        sa.Column(
            "embedding",
            Vector(384),
            nullable=False,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index on topic_id for fast lookups
    op.create_index("ix_topic_embedding_topic_id", "topic_embedding", ["topic_id"])

    # HNSW index for fast cosine similarity search
    op.execute(
        """
        CREATE INDEX ix_topic_embedding_embedding_hnsw
        ON topic_embedding
        USING hnsw (embedding vector_cosine_ops)
        """
    )

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_topic_embedding_updated_at
        BEFORE UPDATE ON topic_embedding
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )


def downgrade() -> None:
    # Drop triggers first
    op.execute(
        "DROP TRIGGER IF EXISTS update_topic_embedding_updated_at ON topic_embedding"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_mentor_embedding_updated_at ON mentor_embedding"
    )
    op.execute("DROP TRIGGER IF EXISTS update_topic_updated_at ON topic")

    # Drop tables (indexes and constraints are dropped automatically)
    op.drop_table("topic_embedding")
    op.drop_table("mentor_embedding")
    op.drop_table("mentor_topic")
    op.drop_table("topic")
