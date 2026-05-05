"""Initial base infrastructure: pgvector, trigger function, UUID helper.

Revision ID: 0001
Revises:
Create Date: 2025-05-05

This migration sets up foundational database infrastructure:
- pgvector extension for vector similarity search
- update_updated_at() trigger function for automatic timestamp updates
- generate_uuid() helper function wrapping gen_random_uuid()
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension for vector similarity search
    # Required for embedding storage and cosine similarity queries
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create reusable trigger function for updating updated_at columns
    # Apply to any table with: CREATE TRIGGER ... EXECUTE FUNCTION update_updated_at()
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Create UUID generation helper function
    # Wraps PostgreSQL's built-in gen_random_uuid() for consistency
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_uuid()
        RETURNS UUID AS $$
        BEGIN
            RETURN gen_random_uuid();
        END;
        $$ LANGUAGE plpgsql
    """)


def downgrade() -> None:
    # Drop functions in reverse order
    op.execute("DROP FUNCTION IF EXISTS generate_uuid()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")

    # Drop pgvector extension
    # Note: This will fail if any tables use vector columns
    op.execute("DROP EXTENSION IF EXISTS vector")
