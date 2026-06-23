"""Service layer for mentor recommendations."""

from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.db.models.mentor_profile import MentorProfile
from app.recommender.search import recommend_mentors
from app.schemas.recommendation import (
    RecommendationsResponse,
    RecommendedMentorResponse,
)


def _cache_key(user_id: UUID, topic_id: UUID) -> str:
    return f"recommendations:{user_id}:{topic_id}"


def _serialize_recommendations(response: RecommendationsResponse) -> str:
    return response.model_dump_json()


def _deserialize_recommendations(data: str) -> RecommendationsResponse:
    return RecommendationsResponse.model_validate_json(data)


async def _get_cached_recommendations(
    redis: Redis,
    user_id: UUID,
    topic_id: UUID,
) -> RecommendationsResponse | None:
    """Retrieve cached recommendations if available."""
    key = _cache_key(user_id, topic_id)
    cached = await redis.get(key)
    if cached is None:
        return None
    response = _deserialize_recommendations(cached)
    response.cached = True
    return response


async def _cache_recommendations(
    redis: Redis,
    user_id: UUID,
    topic_id: UUID,
    response: RecommendationsResponse,
) -> None:
    """Store recommendations in cache with TTL."""
    settings = get_settings()
    key = _cache_key(user_id, topic_id)
    await redis.setex(
        key,
        settings.recommendations_cache_ttl_seconds,
        _serialize_recommendations(response),
    )


async def _hydrate_mentor_profiles(
    db: AsyncSession,
    scored_mentors: list[tuple[UUID, float]],
) -> list[tuple[MentorProfile, float]]:
    """Fetch MentorProfile with User data in a single query.

    Args:
        db: Database session
        scored_mentors: List of (user_id, score) tuples from recommend_mentors

    Returns:
        List of (MentorProfile, score) tuples with User eagerly loaded
    """
    if not scored_mentors:
        return []

    user_ids = [user_id for user_id, _ in scored_mentors]
    score_by_user_id = dict(scored_mentors)

    query = (
        select(MentorProfile)
        .options(joinedload(MentorProfile.user))
        .where(MentorProfile.user_id.in_(user_ids))
    )
    result = await db.execute(query)
    profiles = list(result.scalars().unique().all())

    hydrated: list[tuple[MentorProfile, float]] = []
    for profile in profiles:
        score = score_by_user_id.get(profile.user_id)
        if score is not None:
            hydrated.append((profile, score))

    hydrated.sort(key=lambda x: x[1], reverse=True)
    return hydrated


def _build_response(
    topic_id: UUID,
    hydrated: list[tuple[MentorProfile, float]],
) -> RecommendationsResponse:
    """Build the response schema from hydrated profiles."""
    items: list[RecommendedMentorResponse] = []

    for profile, score in hydrated:
        items.append(
            RecommendedMentorResponse(
                id=profile.id,
                user_id=profile.user_id,
                display_name=profile.user.display_name if profile.user else None,
                avatar_url=profile.user.avatar_url if profile.user else None,
                headline=profile.headline,
                bio=profile.bio,
                rating_avg=profile.rating_avg,
                rating_count=profile.rating_count,
                score=score,
            )
        )

    return RecommendationsResponse(
        items=items,
        topic_id=topic_id,
        cached=False,
    )


async def get_recommendations(
    db: AsyncSession,
    redis: Redis,
    user_id: UUID,
    topic_id: UUID,
    limit: int = 20,
) -> RecommendationsResponse:
    """Get mentor recommendations for a user and topic.

    Checks cache first, then computes recommendations if not cached.
    Results are cached for subsequent requests.

    Args:
        db: Database session
        redis: Redis client
        user_id: The requesting user's ID
        topic_id: The topic to find mentors for
        limit: Maximum number of recommendations to return

    Returns:
        RecommendationsResponse with ranked mentors
    """
    cached = await _get_cached_recommendations(redis, user_id, topic_id)
    if cached is not None:
        return cached

    scored_mentors = await recommend_mentors(db, user_id, topic_id, limit)

    hydrated = await _hydrate_mentor_profiles(db, scored_mentors)

    response = _build_response(topic_id, hydrated)

    await _cache_recommendations(redis, user_id, topic_id, response)

    return response
