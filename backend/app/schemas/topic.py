"""Pydantic schemas for topic endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopicResponse(BaseModel):
    """Full topic detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    parent_topic_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class TopicListResponse(BaseModel):
    """Paginated list of topics."""

    items: list[TopicResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class MentorBriefResponse(BaseModel):
    """Mentor info for topic mentor lists."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    headline: str | None = None
    rating_avg: Decimal | None = None
    rating_count: int


class TopicMentorsResponse(BaseModel):
    """Paginated list of mentors for a topic."""

    items: list[MentorBriefResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class TopicSearchResult(BaseModel):
    """Topic with similarity score for search results."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    similarity: float = Field(..., ge=0.0, le=1.0)


class TopicSearchResponse(BaseModel):
    """Search results with similarity scores."""

    items: list[TopicSearchResult]
    query: str
