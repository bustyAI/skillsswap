"""Tests for the mentor recommendation system."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.block import Block
from app.db.models.mentor_embedding import MentorEmbedding
from app.db.models.mentor_profile import MentorProfile
from app.db.models.report import Report, ReportStatus
from app.db.models.topic import Topic
from app.db.models.topic_embedding import TopicEmbedding
from app.db.models.user import User
from app.recommender.embeddings import encode
from app.recommender.search import (
    _compute_activity_recency,
    _compute_moderation_penalty,
    _compute_normalized_rating,
    recommend_mentors,
)


class TestHelperFunctions:
    def test_activity_recency_none_returns_default(self) -> None:
        assert _compute_activity_recency(None) == 0.5

    def test_activity_recency_recent_is_high(self) -> None:
        now = datetime.now(UTC)
        result = _compute_activity_recency(now)
        assert result > 0.9

    def test_activity_recency_old_is_low(self) -> None:
        old = datetime.now(UTC) - timedelta(days=90)
        result = _compute_activity_recency(old)
        assert result < 0.2

    def test_normalized_rating_low_count_returns_default(self) -> None:
        assert _compute_normalized_rating(Decimal("4.5"), 2) == 0.5

    def test_normalized_rating_none_returns_default(self) -> None:
        assert _compute_normalized_rating(None, 5) == 0.5

    def test_normalized_rating_computes_correctly(self) -> None:
        result = _compute_normalized_rating(Decimal("4.0"), 10)
        assert result == 0.8

    def test_moderation_penalty_zero_reports(self) -> None:
        assert _compute_moderation_penalty(0) == 0.0

    def test_moderation_penalty_capped_at_one(self) -> None:
        assert _compute_moderation_penalty(15) == 1.0

    def test_moderation_penalty_scales_linearly(self) -> None:
        assert _compute_moderation_penalty(5) == 0.5


async def _create_user(
    db: AsyncSession,
    email: str,
    cognito_sub: str | None = None,
    banned_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> User:
    user = User(
        cognito_sub=cognito_sub or str(uuid4()),
        email=email,
        display_name=email.split("@")[0],
        banned_at=banned_at,
        deleted_at=deleted_at,
    )
    db.add(user)
    await db.flush()
    return user


async def _create_mentor_profile(
    db: AsyncSession,
    user: User,
    bio: str = "Test mentor bio",
    is_enabled: bool = True,
    rating_avg: Decimal | None = None,
    rating_count: int = 0,
    last_active_at: datetime | None = None,
) -> MentorProfile:
    profile = MentorProfile(
        user_id=user.id,
        bio=bio,
        headline="Test headline",
        is_enabled=is_enabled,
        rating_avg=rating_avg,
        rating_count=rating_count,
        last_active_at=last_active_at,
    )
    db.add(profile)
    await db.flush()
    return profile


async def _create_mentor_embedding(
    db: AsyncSession,
    profile: MentorProfile,
    text: str,
) -> MentorEmbedding:
    embedding = MentorEmbedding(
        mentor_profile_id=profile.id,
        embedding=encode(text),
    )
    db.add(embedding)
    await db.flush()
    return embedding


async def _create_topic_with_embedding(
    db: AsyncSession,
    name: str,
    description: str = "Test description",
) -> Topic:
    topic = Topic(name=name, description=description)
    db.add(topic)
    await db.flush()

    topic_embedding = TopicEmbedding(
        topic_id=topic.id,
        embedding=encode(f"{name} {description}"),
    )
    db.add(topic_embedding)
    await db.flush()
    return topic


@pytest.mark.asyncio
async def test_recommend_mentors_ranking(async_session: AsyncSession) -> None:
    """Test that mentors are ranked correctly by the scoring formula."""
    requesting_user = await _create_user(async_session, "requester@test.com")
    topic = await _create_topic_with_embedding(
        async_session, "Python Programming", "Learn Python development"
    )

    # Mentor A: High similarity (Python expert), good rating, recent activity
    user_a = await _create_user(async_session, "mentor_a@test.com")
    profile_a = await _create_mentor_profile(
        async_session,
        user_a,
        bio="Python programming expert",
        rating_avg=Decimal("4.8"),
        rating_count=10,
        last_active_at=datetime.now(UTC),
    )
    await _create_mentor_embedding(
        async_session, profile_a, "Python programming expert developer"
    )

    # Mentor B: Medium similarity, lower rating, older activity
    user_b = await _create_user(async_session, "mentor_b@test.com")
    profile_b = await _create_mentor_profile(
        async_session,
        user_b,
        bio="General software developer",
        rating_avg=Decimal("3.5"),
        rating_count=5,
        last_active_at=datetime.now(UTC) - timedelta(days=60),
    )
    await _create_mentor_embedding(
        async_session, profile_b, "General software development coding"
    )

    # Mentor C: Low similarity (unrelated topic), high rating
    user_c = await _create_user(async_session, "mentor_c@test.com")
    profile_c = await _create_mentor_profile(
        async_session,
        user_c,
        bio="Professional chef",
        rating_avg=Decimal("5.0"),
        rating_count=20,
        last_active_at=datetime.now(UTC),
    )
    await _create_mentor_embedding(
        async_session, profile_c, "Cooking culinary arts chef restaurant"
    )

    await async_session.commit()

    results = await recommend_mentors(
        async_session, requesting_user.id, topic.id, limit=10
    )

    assert len(results) == 3
    result_user_ids = [r[0] for r in results]

    # Mentor A should rank highest (high similarity to Python topic)
    assert result_user_ids[0] == user_a.id
    # Mentor B should rank second (some tech relevance)
    assert result_user_ids[1] == user_b.id
    # Mentor C should rank last (cooking has no relevance to Python)
    assert result_user_ids[2] == user_c.id


@pytest.mark.asyncio
async def test_recommend_mentors_filters_disabled_profile(
    async_session: AsyncSession,
) -> None:
    """Test that disabled mentor profiles are excluded."""
    requesting_user = await _create_user(async_session, "requester@test.com")
    topic = await _create_topic_with_embedding(async_session, "Testing")

    user = await _create_user(async_session, "disabled@test.com")
    profile = await _create_mentor_profile(
        async_session, user, bio="Test mentor", is_enabled=False
    )
    await _create_mentor_embedding(async_session, profile, "Testing software QA")
    await async_session.commit()

    results = await recommend_mentors(
        async_session, requesting_user.id, topic.id, limit=10
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_recommend_mentors_filters_banned_user(
    async_session: AsyncSession,
) -> None:
    """Test that banned users are excluded from recommendations."""
    requesting_user = await _create_user(async_session, "requester@test.com")
    topic = await _create_topic_with_embedding(async_session, "Testing")

    banned_user = await _create_user(
        async_session, "banned@test.com", banned_at=datetime.now(UTC)
    )
    profile = await _create_mentor_profile(
        async_session, banned_user, bio="Banned mentor"
    )
    await _create_mentor_embedding(async_session, profile, "Testing software QA")
    await async_session.commit()

    results = await recommend_mentors(
        async_session, requesting_user.id, topic.id, limit=10
    )

    assert len(results) == 0
