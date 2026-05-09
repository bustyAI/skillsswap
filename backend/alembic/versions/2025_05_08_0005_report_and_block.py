"""Report and Block tables for moderation.

Revision ID: 0005
Revises: 0004
Create Date: 2025-05-08

Creates tables for user moderation:
- report: User-submitted reports for admin review
- block: User blocking another user

Key constraints:
- report: status enum (PENDING, UNDER_REVIEW, RESOLVED, DISMISSED)
- block: UNIQUE(blocker_id, blocked_id), CHECK(blocker_id <> blocked_id)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # === REPORT TABLE ===
    op.create_table(
        "report",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # Who filed the report
        sa.Column(
            "reporter_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # What/who is being reported (at least one set at app layer)
        sa.Column(
            "reported_user_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "reported_mentorship_id",
            sa.UUID(),
            sa.ForeignKey("mentorship.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # Report content
        sa.Column("reason", sa.Text(), nullable=False),
        # Status enum
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "UNDER_REVIEW",
                "RESOLVED",
                "DISMISSED",
                name="report_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        # Resolution details
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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

    # Indexes for report lookups
    op.create_index("ix_report_reporter_id", "report", ["reporter_id"])
    op.create_index("ix_report_reported_user_id", "report", ["reported_user_id"])
    op.create_index(
        "ix_report_reported_mentorship_id", "report", ["reported_mentorship_id"]
    )
    op.create_index("ix_report_resolved_by_id", "report", ["resolved_by_id"])
    op.create_index("ix_report_status", "report", ["status"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_report_updated_at
        BEFORE UPDATE ON report
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === BLOCK TABLE ===
    op.create_table(
        "block",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # Who is blocking whom
        sa.Column(
            "blocker_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "blocked_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Timestamp (no updated_at - blocks are create/delete only)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.UniqueConstraint(
            "blocker_id", "blocked_id", name="uq_block_blocker_blocked"
        ),
        sa.CheckConstraint("blocker_id <> blocked_id", name="ck_block_no_self_block"),
    )

    # Indexes for block lookups
    op.create_index("ix_block_blocker_id", "block", ["blocker_id"])
    op.create_index("ix_block_blocked_id", "block", ["blocked_id"])


def downgrade() -> None:
    # Drop updated_at trigger
    op.execute("DROP TRIGGER IF EXISTS update_report_updated_at ON report")

    # Drop tables
    op.drop_table("block")
    op.drop_table("report")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS report_status")
