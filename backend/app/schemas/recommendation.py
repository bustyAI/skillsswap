"""Pydantic schemas for recommendation endpoints."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecommendedMentorResponse(BaseModel):
    """A mentor recommendation with relevance score."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None
    headline: str | None = None
    bio: str | None = None
    rating_avg: Decimal | None = None
    rating_count: int
    score: float = Field(..., ge=0.0, le=1.0)


class RecommendationsResponse(BaseModel):
    """Response containing ranked mentor recommendations."""

    items: list[RecommendedMentorResponse]
    topic_id: UUID
    cached: bool = False
