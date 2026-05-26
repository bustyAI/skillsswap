"""Pydantic schemas for MentorProfile endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MentorProfileCreate(BaseModel):
    """Fields for creating a mentor profile."""

    bio: str | None = Field(default=None, max_length=5000)
    headline: str | None = Field(default=None, max_length=200)


class MentorProfileUpdate(BaseModel):
    """Fields that can be updated on a mentor profile."""

    bio: str | None = Field(default=None, max_length=5000)
    headline: str | None = Field(default=None, max_length=200)


class MentorProfileResponse(BaseModel):
    """Mentor profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    bio: str | None = None
    headline: str | None = None
    is_enabled: bool
    rating_avg: Decimal | None = None
    rating_count: int
    last_active_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TopicBrief(BaseModel):
    """Minimal topic info for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class MentorTopicsUpdate(BaseModel):
    """Request body for replacing mentor's topic list."""

    topic_ids: list[UUID] = Field(..., max_length=20)


class MentorTopicsResponse(BaseModel):
    """Response for mentor's topic list."""

    topics: list[TopicBrief]
