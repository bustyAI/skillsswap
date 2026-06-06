"""Add audit_log table and user.banned_at column.

Revision ID: 0007
Revises: 0006
Create Date: 2025-06-05

Adds:
- audit_log table for append-only admin action logging
- banned_at column to user table for tracking banned users
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE audit_action AS ENUM (
            'BAN_USER',
            'UNBAN_USER',
            'DISABLE_MENTOR',
            'ENABLE_MENTOR',
            'RESOLVE_REPORT',
            'DISMISS_REPORT',
            'DELETE_USER'
        )
        """
    )

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("admin_id", sa.UUID(), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "BAN_USER",
                "UNBAN_USER",
                "DISABLE_MENTOR",
                "ENABLE_MENTOR",
                "RESOLVE_REPORT",
                "DISMISS_REPORT",
                "DELETE_USER",
                name="audit_action",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("target_user_id", sa.UUID(), nullable=True),
        sa.Column("target_report_id", sa.UUID(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["user.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["user.id"],
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_audit_log_admin_id", "audit_log", ["admin_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_target_user_id", "audit_log", ["target_user_id"])
    op.create_index("ix_audit_log_target_report_id", "audit_log", ["target_report_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.add_column(
        "user",
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_banned_at", "user", ["banned_at"])


def downgrade() -> None:
    op.drop_index("ix_user_banned_at", table_name="user")
    op.drop_column("user", "banned_at")

    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_target_report_id", table_name="audit_log")
    op.drop_index("ix_audit_log_target_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_admin_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.execute("DROP TYPE audit_action")
