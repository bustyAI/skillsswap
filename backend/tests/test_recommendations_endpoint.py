"""Tests for the recommendations endpoint."""

from collections.abc import Callable
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimitExceeded, check_rate_limit
from app.db.models.mentor_embedding import MentorEmbedding
from app.db.models.mentor_profile import MentorProfile
from app.db.models.topic import Topic
from app.db.models.topic_embedding import TopicEmbedding
from app.db.models.user import User
from app.recommender.embeddings import encode
from app.schemas.recommendation import RecommendationsResponse
from app.services.recommendation_service import (
    _cache_key,
    _get_cached_recommendations,
    get_recommendations,
)


class TestRecommendationsAuth:
    """Tests for authentication on the recommendations endpoint."""

    def test_no_auth_returns_401(self, client: TestClient) -> None:
        """Request without Authorization header returns 401."""
        response = client.get("/api/recommendations", params={"topic_id": str(uuid4())})
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        """Request with invalid token returns 401."""
        response = client.get(
            "/api/recommendations",
            params={"topic_id": str(uuid4())},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """Expired token returns 401."""
        token = make_token(exp_offset=-3600)
        response = client.get(
            "/api/recommendations",
            params={"topic_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_rate_limit_increments_counter(self) -> None:
        """Rate limit counter increments on each call."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(side_effect=[1, 2, 3])
        mock_redis.expire = AsyncMock()

        count1 = await check_rate_limit(
            mock_redis, "test:key", limit=10, window_seconds=60
        )
        count2 = await check_rate_limit(
            mock_redis, "test:key", limit=10, window_seconds=60
        )
        count3 = await check_rate_limit(
            mock_redis, "test:key", limit=10, window_seconds=60
        )

        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    @pytest.mark.asyncio
    async def test_rate_limit_sets_expiry_on_first_request(self) -> None:
        """Expiry is set only on first request (when counter is 1)."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        await check_rate_limit(mock_redis, "test:key", limit=10, window_seconds=60)

        mock_redis.expire.assert_called_once_with("test:key", 60)

    @pytest.mark.asyncio
    async def test_rate_limit_does_not_set_expiry_on_subsequent_requests(self) -> None:
        """Expiry is not reset on subsequent requests."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=5)
        mock_redis.expire = AsyncMock()

        await check_rate_limit(mock_redis, "test:key", limit=10, window_seconds=60)

        mock_redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_raises_exception(self) -> None:
        """Exceeding rate limit raises RateLimitExceeded."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=31)
        mock_redis.ttl = AsyncMock(return_value=45)

        with pytest.raises(RateLimitExceeded) as exc_info:
            await check_rate_limit(mock_redis, "test:key", limit=30, window_seconds=60)

        assert exc_info.value.retry_after == 45

    @pytest.mark.asyncio
    async def test_rate_limit_at_limit_passes(self) -> None:
        """Request at exactly the limit passes."""
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=30)

        count = await check_rate_limit(
            mock_redis, "test:key", limit=30, window_seconds=60
        )
        assert count == 30


class TestCaching:
    """Tests for recommendation caching behavior."""

    def test_cache_key_format(self) -> None:
        """Cache key follows expected format."""
        user_id = uuid4()
        topic_id = uuid4()
        key = _cache_key(user_id, topic_id)
        assert key == f"recommendations:{user_id}:{topic_id}"

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self) -> None:
        """Cache miss returns None."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        result = await _get_cached_recommendations(mock_redis, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_returns_response_with_cached_flag(self) -> None:
        """Cache hit returns response with cached=True."""
        mock_redis = AsyncMock()
        cached_data = RecommendationsResponse(
            items=[],
            topic_id=uuid4(),
            cached=False,
        )
        mock_redis.get = AsyncMock(return_value=cached_data.model_dump_json())

        result = await _get_cached_recommendations(
            mock_redis, uuid4(), cached_data.topic_id
        )

        assert result is not None
        assert result.cached is True


async def _create_test_user(
    db: AsyncSession,
    email: str,
) -> User:
    user = User(
        cognito_sub=str(uuid4()),
        email=email,
        display_name=email.split("@")[0],
    )
    db.add(user)
    await db.flush()
    return user


async def _create_mentor_with_embedding(
    db: AsyncSession,
    user: User,
    bio: str,
    rating_avg: Decimal | None = None,
    rating_count: int = 0,
) -> MentorProfile:
    profile = MentorProfile(
        user_id=user.id,
        bio=bio,
        headline="Test headline",
        is_enabled=True,
        rating_avg=rating_avg,
        rating_count=rating_count,
    )
    db.add(profile)
    await db.flush()

    embedding = MentorEmbedding(
        mentor_profile_id=profile.id,
        embedding=encode(bio),
    )
    db.add(embedding)
    await db.flush()
    return profile


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


class TestGetRecommendationsService:
    """Tests for the get_recommendations service function."""

    @pytest.mark.asyncio
    async def test_returns_ranked_mentors(self, async_session: AsyncSession) -> None:
        """Service returns mentors ranked by score."""
        requesting_user = await _create_test_user(async_session, "requester@test.com")
        topic = await _create_topic_with_embedding(
            async_session, "Python", "Python programming language"
        )

        mentor_user = await _create_test_user(async_session, "mentor@test.com")
        await _create_mentor_with_embedding(
            async_session,
            mentor_user,
            bio="Python expert developer",
            rating_avg=Decimal("4.5"),
            rating_count=10,
        )
        await async_session.commit()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        response = await get_recommendations(
            db=async_session,
            redis=mock_redis,
            user_id=requesting_user.id,
            topic_id=topic.id,
            limit=10,
        )

        assert len(response.items) == 1
        assert response.items[0].user_id == mentor_user.id
        assert response.items[0].score > 0
        assert response.cached is False

    @pytest.mark.asyncio
    async def test_caches_result_after_computation(
        self, async_session: AsyncSession
    ) -> None:
        """Service caches results after computing them."""
        requesting_user = await _create_test_user(async_session, "requester@test.com")
        topic = await _create_topic_with_embedding(async_session, "Caching Test")
        await async_session.commit()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        await get_recommendations(
            db=async_session,
            redis=mock_redis,
            user_id=requesting_user.id,
            topic_id=topic.id,
        )

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == _cache_key(requesting_user.id, topic.id)
        assert call_args[0][1] == 300

    @pytest.mark.asyncio
    async def test_returns_cached_result_on_hit(
        self, async_session: AsyncSession
    ) -> None:
        """Service returns cached result without hitting DB."""
        requesting_user = await _create_test_user(async_session, "requester@test.com")
        topic = await _create_topic_with_embedding(async_session, "Cache Hit Test")
        await async_session.commit()

        cached_response = RecommendationsResponse(
            items=[],
            topic_id=topic.id,
            cached=False,
        )

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_response.model_dump_json())

        response = await get_recommendations(
            db=async_session,
            redis=mock_redis,
            user_id=requesting_user.id,
            topic_id=topic.id,
        )

        assert response.cached is True
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_result_when_no_mentors(
        self, async_session: AsyncSession
    ) -> None:
        """Returns empty list when no mentors match the topic."""
        requesting_user = await _create_test_user(async_session, "requester@test.com")
        topic = await _create_topic_with_embedding(
            async_session, "Obscure Topic", "No mentors for this"
        )
        await async_session.commit()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        response = await get_recommendations(
            db=async_session,
            redis=mock_redis,
            user_id=requesting_user.id,
            topic_id=topic.id,
        )

        assert len(response.items) == 0
        assert response.topic_id == topic.id

    @pytest.mark.asyncio
    async def test_hydrates_user_data(self, async_session: AsyncSession) -> None:
        """Response includes user display_name and avatar_url."""
        requesting_user = await _create_test_user(async_session, "requester@test.com")
        topic = await _create_topic_with_embedding(async_session, "Hydration Test")

        mentor_user = await _create_test_user(async_session, "mentor@test.com")
        mentor_user.display_name = "Expert Mentor"
        mentor_user.avatar_url = "https://example.com/avatar.png"
        await _create_mentor_with_embedding(
            async_session, mentor_user, bio="Hydration test mentor"
        )
        await async_session.commit()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        response = await get_recommendations(
            db=async_session,
            redis=mock_redis,
            user_id=requesting_user.id,
            topic_id=topic.id,
        )

        assert len(response.items) == 1
        assert response.items[0].display_name == "Expert Mentor"
        assert response.items[0].avatar_url == "https://example.com/avatar.png"
