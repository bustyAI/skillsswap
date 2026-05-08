"""Mentorship, Meeting, Messaging, and Review tables.

Revision ID: 0004
Revises: 0003
Create Date: 2025-05-07

Creates tables for mentorship relationships and reviews:
- mentorship: Mentor-mentee relationships with status tracking
- meeting: Scheduled sessions within a mentorship
- message_thread: Container for messages in a mentorship
- message: Individual messages in a thread
- review: Mentee reviews of completed meetings

Key constraints:
- mentorship: UNIQUE(mentor_id, mentee_id), CHECK(mentor_id <> mentee_id)
- meeting: CHECK that SCHEDULED status requires scheduled_time AND meeting_url
- review: UNIQUE(meeting_id), CHECK(rating BETWEEN 1 AND 5)

Also creates a trigger to update mentor_profile.rating_avg and rating_count
whenever a review is inserted or updated.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # === MENTORSHIP TABLE ===
    # Note: sa.Enum() will auto-create the mentorship_status type
    op.create_table(
        "mentorship",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to mentor (user)
        sa.Column(
            "mentor_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # FK to mentee (user)
        sa.Column(
            "mentee_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Status enum
        sa.Column(
            "status",
            sa.Enum(
                "REQUESTED",
                "ACTIVE",
                "ENDED",
                "DECLINED",
                name="mentorship_status",
            ),
            nullable=False,
            server_default="REQUESTED",
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
        # Constraints
        sa.UniqueConstraint(
            "mentor_id", "mentee_id", name="uq_mentorship_mentor_mentee"
        ),
        sa.CheckConstraint(
            "mentor_id <> mentee_id", name="ck_mentorship_no_self_mentorship"
        ),
    )

    # Indexes for fast lookups by mentor or mentee
    op.create_index("ix_mentorship_mentor_id", "mentorship", ["mentor_id"])
    op.create_index("ix_mentorship_mentee_id", "mentorship", ["mentee_id"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_mentorship_updated_at
        BEFORE UPDATE ON mentorship
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === MEETING TABLE ===
    op.create_table(
        "meeting",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to mentorship
        sa.Column(
            "mentorship_id",
            sa.UUID(),
            sa.ForeignKey("mentorship.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Scheduled time (required when status is SCHEDULED)
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        # Meeting URL (required when status is SCHEDULED)
        sa.Column("meeting_url", sa.String(500), nullable=True),
        # Status enum
        sa.Column(
            "status",
            sa.Enum(
                "REQUESTED",
                "SCHEDULED",
                "COMPLETED",
                "CANCELLED",
                name="meeting_status",
            ),
            nullable=False,
            server_default="REQUESTED",
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
        # CHECK: SCHEDULED status requires both scheduled_time and meeting_url
        sa.CheckConstraint(
            "(status != 'SCHEDULED') OR (scheduled_time IS NOT NULL AND meeting_url IS NOT NULL)",
            name="ck_meeting_scheduled_requires_time_and_url",
        ),
    )

    # Index for fast lookups by mentorship
    op.create_index("ix_meeting_mentorship_id", "meeting", ["mentorship_id"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_meeting_updated_at
        BEFORE UPDATE ON meeting
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === MESSAGE_THREAD TABLE ===
    op.create_table(
        "message_thread",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to mentorship - UNIQUE (one thread per mentorship)
        sa.Column(
            "mentorship_id",
            sa.UUID(),
            sa.ForeignKey("mentorship.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
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

    # Index on mentorship_id
    op.create_index(
        "ix_message_thread_mentorship_id", "message_thread", ["mentorship_id"]
    )

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_message_thread_updated_at
        BEFORE UPDATE ON message_thread
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === MESSAGE TABLE ===
    op.create_table(
        "message",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to message_thread
        sa.Column(
            "thread_id",
            sa.UUID(),
            sa.ForeignKey("message_thread.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # FK to sender (user) - nullable for system messages
        sa.Column(
            "sender_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Message content
        sa.Column("content", sa.Text(), nullable=False),
        # Is this a system message?
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
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

    # Indexes for fast lookups
    op.create_index("ix_message_thread_id", "message", ["thread_id"])
    op.create_index("ix_message_sender_id", "message", ["sender_id"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_message_updated_at
        BEFORE UPDATE ON message
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === REVIEW TABLE ===
    op.create_table(
        "review",
        # Primary key
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # FK to meeting - UNIQUE (one review per meeting)
        sa.Column(
            "meeting_id",
            sa.UUID(),
            sa.ForeignKey("meeting.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # FK to reviewer (the mentee)
        sa.Column(
            "reviewer_id",
            sa.UUID(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Rating 1-5
        sa.Column("rating", sa.Integer(), nullable=False),
        # Optional comment
        sa.Column("comment", sa.Text(), nullable=True),
        # Edit window deadline
        sa.Column("editable_until", sa.DateTime(timezone=True), nullable=False),
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
        # CHECK: rating must be between 1 and 5
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_review_rating_range"
        ),
    )

    # Indexes for fast lookups
    op.create_index("ix_review_meeting_id", "review", ["meeting_id"])
    op.create_index("ix_review_reviewer_id", "review", ["reviewer_id"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE TRIGGER update_review_updated_at
        BEFORE UPDATE ON review
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at()
        """
    )

    # === TRIGGER FUNCTION FOR MENTOR RATING AGGREGATION ===
    # This function recalculates rating_avg and rating_count for a mentor
    # whenever a review is inserted or updated.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_mentor_rating_stats()
        RETURNS TRIGGER AS $$
        DECLARE
            v_mentor_profile_id UUID;
            v_rating_avg NUMERIC(3,2);
            v_rating_count INTEGER;
        BEGIN
            -- Find the mentor_profile_id by traversing:
            -- review -> meeting -> mentorship -> mentor_id -> mentor_profile
            SELECT mp.id INTO v_mentor_profile_id
            FROM mentor_profile mp
            JOIN mentorship ms ON ms.mentor_id = mp.user_id
            JOIN meeting mt ON mt.mentorship_id = ms.id
            WHERE mt.id = NEW.meeting_id;

            -- If we found a mentor profile, recalculate their stats
            IF v_mentor_profile_id IS NOT NULL THEN
                -- Calculate average and count from all reviews for this mentor
                SELECT
                    COALESCE(AVG(r.rating)::NUMERIC(3,2), 0),
                    COUNT(r.id)::INTEGER
                INTO v_rating_avg, v_rating_count
                FROM review r
                JOIN meeting mt ON mt.id = r.meeting_id
                JOIN mentorship ms ON ms.id = mt.mentorship_id
                JOIN mentor_profile mp ON mp.user_id = ms.mentor_id
                WHERE mp.id = v_mentor_profile_id;

                -- Update the mentor profile
                UPDATE mentor_profile
                SET
                    rating_avg = v_rating_avg,
                    rating_count = v_rating_count,
                    updated_at = now()
                WHERE id = v_mentor_profile_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Create the trigger on review table
    op.execute(
        """
        CREATE TRIGGER trigger_update_mentor_rating_stats
        AFTER INSERT OR UPDATE ON review
        FOR EACH ROW
        EXECUTE FUNCTION update_mentor_rating_stats()
        """
    )


def downgrade() -> None:
    # Drop the rating stats trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_update_mentor_rating_stats ON review")
    op.execute("DROP FUNCTION IF EXISTS update_mentor_rating_stats()")

    # Drop updated_at triggers
    op.execute("DROP TRIGGER IF EXISTS update_review_updated_at ON review")
    op.execute("DROP TRIGGER IF EXISTS update_message_updated_at ON message")
    op.execute(
        "DROP TRIGGER IF EXISTS update_message_thread_updated_at ON message_thread"
    )
    op.execute("DROP TRIGGER IF EXISTS update_meeting_updated_at ON meeting")
    op.execute("DROP TRIGGER IF EXISTS update_mentorship_updated_at ON mentorship")

    # Drop tables in reverse order (respecting FK dependencies)
    op.drop_table("review")
    op.drop_table("message")
    op.drop_table("message_thread")
    op.drop_table("meeting")
    op.drop_table("mentorship")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS meeting_status")
    op.execute("DROP TYPE IF EXISTS mentorship_status")
