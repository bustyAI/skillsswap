"""Tests for User and MentorProfile models.

These tests verify database-level constraints:
- Partial unique index on user.email (unique only when deleted_at IS NULL)
- Soft-delete filtering via soft_delete_select helper
- One-to-one relationship between User and MentorProfile

Run with: uv run pytest tests/test_user_model.py -v
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import soft_delete_select
from app.db.models import MentorProfile, User


class TestUserEmailUniqueness:
    """Test the partial unique index on user.email."""

    async def test_cannot_create_two_active_users_with_same_email(
        self, async_session: AsyncSession
    ) -> None:
        """Two active users cannot have the same email.

        The partial unique index (WHERE deleted_at IS NULL) should
        prevent this at the database level.
        """
        email = "duplicate@example.com"

        # Create first user
        user1 = User(
            cognito_sub=f"cognito-{uuid4()}",
            email=email,
        )
        async_session.add(user1)
        await async_session.commit()

        # Attempt to create second user with same email
        user2 = User(
            cognito_sub=f"cognito-{uuid4()}",
            email=email,
        )
        async_session.add(user2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        # Verify it's the right constraint
        assert "ix_user_email_active" in str(exc_info.value)

    async def test_can_create_user_with_same_email_after_soft_delete(
        self, async_session: AsyncSession
    ) -> None:
        """A soft-deleted user's email can be reused by a new user.

        The partial unique index only applies to active users
        (deleted_at IS NULL), so after soft-deleting user1,
        user2 can use the same email.
        """
        email = "reusable@example.com"

        # Create and soft-delete first user
        user1 = User(
            cognito_sub=f"cognito-{uuid4()}",
            email=email,
        )
        async_session.add(user1)
        await async_session.commit()

        # Soft-delete user1 by setting deleted_at
        user1.deleted_at = datetime.now(UTC)
        await async_session.commit()

        # Now create user2 with the same email - should succeed
        user2 = User(
            cognito_sub=f"cognito-{uuid4()}",
            email=email,
        )
        async_session.add(user2)
        await async_session.commit()

        # Verify both users exist
        result = await async_session.execute(select(User).where(User.email == email))
        users = result.scalars().all()
        assert len(users) == 2

        # Verify one is deleted, one is active
        deleted_users = [u for u in users if u.deleted_at is not None]
        active_users = [u for u in users if u.deleted_at is None]
        assert len(deleted_users) == 1
        assert len(active_users) == 1


class TestSoftDeleteFilter:
    """Test the soft_delete_select helper function."""

    async def test_soft_delete_select_filters_deleted_users(
        self, async_session: AsyncSession
    ) -> None:
        """soft_delete_select should only return active users.

        Users with deleted_at set should be filtered out.
        """
        # Create an active user
        active_user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="active@example.com",
        )
        async_session.add(active_user)

        # Create a soft-deleted user
        deleted_user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="deleted@example.com",
            deleted_at=datetime.now(UTC),
        )
        async_session.add(deleted_user)

        await async_session.commit()

        # Query using soft_delete_select (should filter deleted users)
        result = await async_session.execute(soft_delete_select(User))
        users = result.scalars().all()

        # Only the active user should be returned
        emails = [u.email for u in users]
        assert "active@example.com" in emails
        assert "deleted@example.com" not in emails

    async def test_regular_select_returns_all_users(
        self, async_session: AsyncSession
    ) -> None:
        """Regular select() returns both active and deleted users.

        This verifies that the filtering is opt-in via soft_delete_select,
        not automatic on all queries.
        """
        # Create users
        active_user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="active2@example.com",
        )
        deleted_user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="deleted2@example.com",
            deleted_at=datetime.now(UTC),
        )
        async_session.add_all([active_user, deleted_user])
        await async_session.commit()

        # Query using regular select (no filter)
        result = await async_session.execute(select(User))
        users = result.scalars().all()

        # Both users should be returned
        emails = [u.email for u in users]
        assert "active2@example.com" in emails
        assert "deleted2@example.com" in emails


class TestMentorProfile:
    """Test MentorProfile model and its relationship to User."""

    async def test_create_mentor_profile(self, async_session: AsyncSession) -> None:
        """Can create a MentorProfile for a User."""
        user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="mentor@example.com",
        )
        async_session.add(user)
        await async_session.commit()

        profile = MentorProfile(
            user_id=user.id,
            bio="I am a mentor",
            headline="Senior Developer",
            is_enabled=True,
        )
        async_session.add(profile)
        await async_session.commit()

        # Verify relationship works
        await async_session.refresh(user, ["mentor_profile"])
        assert user.mentor_profile is not None
        assert user.mentor_profile.bio == "I am a mentor"

    async def test_mentor_profile_user_id_unique(
        self, async_session: AsyncSession
    ) -> None:
        """A user can only have one MentorProfile (user_id is unique)."""
        user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="single-profile@example.com",
        )
        async_session.add(user)
        await async_session.commit()

        # Create first profile
        profile1 = MentorProfile(
            user_id=user.id,
            bio="First profile",
        )
        async_session.add(profile1)
        await async_session.commit()

        # Attempt to create second profile for same user
        profile2 = MentorProfile(
            user_id=user.id,
            bio="Second profile",
        )
        async_session.add(profile2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    async def test_mentor_profile_defaults(self, async_session: AsyncSession) -> None:
        """MentorProfile has correct default values."""
        user = User(
            cognito_sub=f"cognito-{uuid4()}",
            email="defaults@example.com",
        )
        async_session.add(user)
        await async_session.commit()

        profile = MentorProfile(user_id=user.id)
        async_session.add(profile)
        await async_session.commit()

        await async_session.refresh(profile)

        # Check defaults
        assert profile.is_enabled is True
        assert profile.rating_count == 0
        assert profile.rating_avg is None
        assert profile.bio is None
        assert profile.headline is None
