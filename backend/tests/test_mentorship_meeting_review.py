"""Tests for Mentorship, Meeting, and Review models.

These tests verify database-level constraints and triggers:
- CHECK constraints reject invalid rows
- UNIQUE constraints enforce business rules
- Rating trigger updates mentor_profile aggregates

Run with: uv run pytest tests/test_mentorship_meeting_review.py -v
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Meeting,
    MeetingStatus,
    MentorProfile,
    Mentorship,
    MentorshipStatus,
    Review,
    User,
)

# =============================================================================
# HELPER FIXTURES
# =============================================================================


async def create_user(session: AsyncSession, email: str | None = None) -> User:
    """Helper to create a user."""
    user = User(
        cognito_sub=f"cognito-{uuid4()}",
        email=email or f"user-{uuid4()}@example.com",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_mentor_with_profile(
    session: AsyncSession, email: str | None = None
) -> tuple[User, MentorProfile]:
    """Helper to create a user with a mentor profile."""
    user = await create_user(session, email)
    profile = MentorProfile(
        user_id=user.id,
        bio="Test mentor bio",
        is_enabled=True,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return user, profile


async def create_mentorship(
    session: AsyncSession,
    mentor: User,
    mentee: User,
    status: MentorshipStatus = MentorshipStatus.ACTIVE,
) -> Mentorship:
    """Helper to create a mentorship."""
    mentorship = Mentorship(
        mentor_id=mentor.id,
        mentee_id=mentee.id,
        status=status,
    )
    session.add(mentorship)
    await session.commit()
    await session.refresh(mentorship)
    return mentorship


async def create_meeting(
    session: AsyncSession,
    mentorship: Mentorship,
    status: MeetingStatus = MeetingStatus.COMPLETED,
    scheduled_time: datetime | None = None,
    meeting_url: str | None = None,
) -> Meeting:
    """Helper to create a meeting."""
    meeting = Meeting(
        mentorship_id=mentorship.id,
        status=status,
        scheduled_time=scheduled_time,
        meeting_url=meeting_url,
    )
    session.add(meeting)
    await session.commit()
    await session.refresh(meeting)
    return meeting


# =============================================================================
# MENTORSHIP CONSTRAINT TESTS
# =============================================================================


class TestMentorshipConstraints:
    """Test CHECK and UNIQUE constraints on mentorship table."""

    async def test_cannot_mentor_yourself(self, async_session: AsyncSession) -> None:
        """CHECK constraint prevents mentor_id == mentee_id.

        A user cannot be their own mentor.
        """
        user = await create_user(async_session)

        mentorship = Mentorship(
            mentor_id=user.id,
            mentee_id=user.id,  # Same as mentor!
            status=MentorshipStatus.REQUESTED,
        )
        async_session.add(mentorship)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "ck_mentorship_no_self_mentorship" in str(exc_info.value)

    async def test_unique_mentor_mentee_pair(self, async_session: AsyncSession) -> None:
        """UNIQUE constraint prevents duplicate mentor-mentee relationships.

        The same mentor-mentee pair cannot have multiple mentorships.
        """
        mentor = await create_user(async_session, "mentor@example.com")
        mentee = await create_user(async_session, "mentee@example.com")

        # Create first mentorship
        mentorship1 = Mentorship(
            mentor_id=mentor.id,
            mentee_id=mentee.id,
            status=MentorshipStatus.ACTIVE,
        )
        async_session.add(mentorship1)
        await async_session.commit()

        # Attempt to create duplicate
        mentorship2 = Mentorship(
            mentor_id=mentor.id,
            mentee_id=mentee.id,
            status=MentorshipStatus.REQUESTED,
        )
        async_session.add(mentorship2)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "uq_mentorship_mentor_mentee" in str(exc_info.value)

    async def test_reverse_mentorship_allowed(
        self, async_session: AsyncSession
    ) -> None:
        """A can mentor B, and B can separately mentor A.

        The unique constraint is on (mentor_id, mentee_id), not unordered pairs.
        """
        user_a = await create_user(async_session, "a@example.com")
        user_b = await create_user(async_session, "b@example.com")

        # A mentors B
        mentorship1 = Mentorship(
            mentor_id=user_a.id,
            mentee_id=user_b.id,
            status=MentorshipStatus.ACTIVE,
        )
        async_session.add(mentorship1)
        await async_session.commit()

        # B mentors A (reverse direction - should be allowed)
        mentorship2 = Mentorship(
            mentor_id=user_b.id,
            mentee_id=user_a.id,
            status=MentorshipStatus.ACTIVE,
        )
        async_session.add(mentorship2)
        await async_session.commit()  # Should succeed

        # Verify both exist
        await async_session.refresh(mentorship1)
        await async_session.refresh(mentorship2)
        assert mentorship1.id != mentorship2.id


# =============================================================================
# MEETING CONSTRAINT TESTS
# =============================================================================


class TestMeetingConstraints:
    """Test CHECK constraints on meeting table."""

    async def test_scheduled_meeting_requires_time_and_url(
        self, async_session: AsyncSession
    ) -> None:
        """CHECK constraint: SCHEDULED status requires scheduled_time AND meeting_url.

        Cannot set status to SCHEDULED without providing both fields.
        """
        mentor = await create_user(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        # Try to create SCHEDULED meeting without time/url
        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.SCHEDULED,
            scheduled_time=None,  # Missing!
            meeting_url=None,  # Missing!
        )
        async_session.add(meeting)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "ck_meeting_scheduled_requires_time_and_url" in str(exc_info.value)

    async def test_scheduled_meeting_requires_url_even_with_time(
        self, async_session: AsyncSession
    ) -> None:
        """SCHEDULED status requires BOTH time and URL, not just time."""
        mentor = await create_user(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.SCHEDULED,
            scheduled_time=datetime.now(UTC) + timedelta(days=1),
            meeting_url=None,  # Missing URL!
        )
        async_session.add(meeting)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "ck_meeting_scheduled_requires_time_and_url" in str(exc_info.value)

    async def test_scheduled_meeting_with_both_fields_succeeds(
        self, async_session: AsyncSession
    ) -> None:
        """SCHEDULED meeting with both time and URL should succeed."""
        mentor = await create_user(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.SCHEDULED,
            scheduled_time=datetime.now(UTC) + timedelta(days=1),
            meeting_url="https://zoom.us/j/123456789",
        )
        async_session.add(meeting)
        await async_session.commit()  # Should succeed

        await async_session.refresh(meeting)
        assert meeting.status == MeetingStatus.SCHEDULED

    async def test_requested_meeting_without_time_url_succeeds(
        self, async_session: AsyncSession
    ) -> None:
        """REQUESTED status does not require time/url."""
        mentor = await create_user(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.REQUESTED,
            scheduled_time=None,
            meeting_url=None,
        )
        async_session.add(meeting)
        await async_session.commit()  # Should succeed

        await async_session.refresh(meeting)
        assert meeting.status == MeetingStatus.REQUESTED


# =============================================================================
# REVIEW CONSTRAINT TESTS
# =============================================================================


class TestReviewConstraints:
    """Test CHECK and UNIQUE constraints on review table."""

    async def test_rating_must_be_at_least_1(self, async_session: AsyncSession) -> None:
        """CHECK constraint: rating >= 1."""
        mentor, _ = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)
        meeting = await create_meeting(async_session, mentorship)

        review = Review(
            meeting_id=meeting.id,
            reviewer_id=mentee.id,
            rating=0,  # Invalid - below minimum!
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "ck_review_rating_range" in str(exc_info.value)

    async def test_rating_must_be_at_most_5(self, async_session: AsyncSession) -> None:
        """CHECK constraint: rating <= 5."""
        mentor, _ = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)
        meeting = await create_meeting(async_session, mentorship)

        review = Review(
            meeting_id=meeting.id,
            reviewer_id=mentee.id,
            rating=6,  # Invalid - above maximum!
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "ck_review_rating_range" in str(exc_info.value)

    async def test_valid_ratings_succeed(self, async_session: AsyncSession) -> None:
        """Ratings 1-5 should all be accepted."""
        mentor, _ = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        for rating in [1, 2, 3, 4, 5]:
            meeting = await create_meeting(async_session, mentorship)
            review = Review(
                meeting_id=meeting.id,
                reviewer_id=mentee.id,
                rating=rating,
                editable_until=datetime.now(UTC) + timedelta(days=7),
            )
            async_session.add(review)
            await async_session.commit()

            await async_session.refresh(review)
            assert review.rating == rating

    async def test_one_review_per_meeting(self, async_session: AsyncSession) -> None:
        """UNIQUE constraint: only one review per meeting."""
        mentor, _ = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)
        meeting = await create_meeting(async_session, mentorship)

        # Create first review
        review1 = Review(
            meeting_id=meeting.id,
            reviewer_id=mentee.id,
            rating=4,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review1)
        await async_session.commit()

        # Attempt duplicate review
        review2 = Review(
            meeting_id=meeting.id,  # Same meeting!
            reviewer_id=mentee.id,
            rating=5,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review2)

        with pytest.raises(IntegrityError) as exc_info:
            await async_session.commit()

        assert "review_meeting_id_key" in str(exc_info.value)


# =============================================================================
# RATING TRIGGER TESTS
# =============================================================================


class TestRatingTrigger:
    """Test the trigger that updates mentor_profile rating aggregates."""

    async def test_trigger_updates_rating_on_first_review(
        self, async_session: AsyncSession
    ) -> None:
        """First review should set rating_avg and rating_count."""
        mentor, profile = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)
        meeting = await create_meeting(async_session, mentorship)

        # Verify initial state
        await async_session.refresh(profile)
        assert profile.rating_avg is None
        assert profile.rating_count == 0

        # Add a review
        review = Review(
            meeting_id=meeting.id,
            reviewer_id=mentee.id,
            rating=4,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review)
        await async_session.commit()

        # Refresh and check - trigger should have updated profile
        await async_session.refresh(profile)
        assert profile.rating_count == 1
        assert profile.rating_avg == Decimal("4.00")

    async def test_trigger_calculates_correct_average_across_3_reviews(
        self, async_session: AsyncSession
    ) -> None:
        """Trigger correctly calculates average across multiple reviews.

        This is the key test from the prompt requirements:
        3 reviews with ratings 3, 4, 5 should give avg = 4.00
        """
        mentor, profile = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)

        ratings = [3, 4, 5]
        expected_avg = Decimal("4.00")  # (3 + 4 + 5) / 3 = 4.0

        for rating in ratings:
            meeting = await create_meeting(async_session, mentorship)
            review = Review(
                meeting_id=meeting.id,
                reviewer_id=mentee.id,
                rating=rating,
                editable_until=datetime.now(UTC) + timedelta(days=7),
            )
            async_session.add(review)
            await async_session.commit()

        # Verify final state
        await async_session.refresh(profile)
        assert profile.rating_count == 3
        assert profile.rating_avg == expected_avg

    async def test_trigger_updates_on_review_update(
        self, async_session: AsyncSession
    ) -> None:
        """Updating a review should recalculate the average."""
        mentor, profile = await create_mentor_with_profile(async_session)
        mentee = await create_user(async_session)
        mentorship = await create_mentorship(async_session, mentor, mentee)
        meeting = await create_meeting(async_session, mentorship)

        # Create initial review with rating 3
        review = Review(
            meeting_id=meeting.id,
            reviewer_id=mentee.id,
            rating=3,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review)
        await async_session.commit()

        await async_session.refresh(profile)
        assert profile.rating_avg == Decimal("3.00")

        # Update the rating to 5
        review.rating = 5
        await async_session.commit()

        # Trigger should recalculate
        await async_session.refresh(profile)
        assert profile.rating_avg == Decimal("5.00")
        assert profile.rating_count == 1

    async def test_trigger_handles_multiple_mentorships(
        self, async_session: AsyncSession
    ) -> None:
        """Trigger correctly aggregates reviews across multiple mentorships.

        A mentor can have multiple mentees, each with their own reviews.
        """
        mentor, profile = await create_mentor_with_profile(async_session)
        mentee1 = await create_user(async_session, "mentee1@example.com")
        mentee2 = await create_user(async_session, "mentee2@example.com")

        # Mentorship with mentee1 - rating 5
        mentorship1 = await create_mentorship(async_session, mentor, mentee1)
        meeting1 = await create_meeting(async_session, mentorship1)
        review1 = Review(
            meeting_id=meeting1.id,
            reviewer_id=mentee1.id,
            rating=5,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review1)
        await async_session.commit()

        # Mentorship with mentee2 - rating 3
        mentorship2 = await create_mentorship(async_session, mentor, mentee2)
        meeting2 = await create_meeting(async_session, mentorship2)
        review2 = Review(
            meeting_id=meeting2.id,
            reviewer_id=mentee2.id,
            rating=3,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review2)
        await async_session.commit()

        # Average should be (5 + 3) / 2 = 4.0
        await async_session.refresh(profile)
        assert profile.rating_count == 2
        assert profile.rating_avg == Decimal("4.00")

    async def test_trigger_isolates_mentor_ratings(
        self, async_session: AsyncSession
    ) -> None:
        """Reviews for one mentor don't affect another mentor's rating."""
        mentor1, profile1 = await create_mentor_with_profile(
            async_session, "mentor1@example.com"
        )
        mentor2, profile2 = await create_mentor_with_profile(
            async_session, "mentor2@example.com"
        )
        mentee = await create_user(async_session, "mentee@example.com")

        # Review for mentor1 - rating 5
        mentorship1 = await create_mentorship(async_session, mentor1, mentee)
        meeting1 = await create_meeting(async_session, mentorship1)
        review1 = Review(
            meeting_id=meeting1.id,
            reviewer_id=mentee.id,
            rating=5,
            editable_until=datetime.now(UTC) + timedelta(days=7),
        )
        async_session.add(review1)
        await async_session.commit()

        # Verify mentor1 has rating, mentor2 does not
        await async_session.refresh(profile1)
        await async_session.refresh(profile2)

        assert profile1.rating_count == 1
        assert profile1.rating_avg == Decimal("5.00")

        assert profile2.rating_count == 0
        assert profile2.rating_avg is None
