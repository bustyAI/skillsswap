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
    display_name: str | None = None
    avatar_url: str | None = None
    headline: str | None = None
    bio: str | None = None
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


class TopicCreate(BaseModel):
    """Schema for creating a topic."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    parent_topic_id: UUID | None = None


class TopicUpdate(BaseModel):
    """Schema for updating a topic."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    parent_topic_id: UUID | None = None
