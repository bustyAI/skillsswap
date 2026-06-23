"""Recommendations endpoint for ML-powered mentor discovery."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.redis import RedisClient
from app.db.dependencies import DbSession
from app.schemas.auth import TokenClaims
from app.schemas.recommendation import RecommendationsResponse
from app.services.recommendation_service import get_recommendations
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

recommendations_limiter = RateLimiter(
    key_prefix="recommendations",
    limit=get_settings().recommendations_rate_limit_per_minute,
    window_seconds=60,
)


@router.get("", response_model=RecommendationsResponse)
async def get_mentor_recommendations(
    db: DbSession,
    redis: RedisClient,
    claims: Annotated[TokenClaims, Depends(get_current_user)],
    topic_id: UUID = Query(..., description="Topic ID to find mentors for"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results to return"),
) -> RecommendationsResponse:
    """Get personalized mentor recommendations for a topic.

    Returns mentors ranked by relevance to the topic, quality metrics,
    and activity recency. Results are cached for 5 minutes per user/topic pair.
    """
    if not claims.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    await recommendations_limiter.check(redis, claims.sub)

    user = await get_or_create_user(db, claims.sub, claims.username)

    return await get_recommendations(
        db=db,
        redis=redis,
        user_id=user.id,
        topic_id=topic_id,
        limit=limit,
    )
