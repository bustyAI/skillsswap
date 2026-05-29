"""Add pg_trgm extension for trigram text search.

Revision ID: 0006
Revises: 0005
Create Date: 2025-05-28

Enables fuzzy text search on topic names using trigram similarity.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_topic_name_trgm ON topic "
        "USING gin (name gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_topic_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
