"""Pydantic schemas for Mentorship endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.mentorship import MentorshipStatus


class UserBrief(BaseModel):
    """Minimal user info for mentorship responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None = None
    email: str


class MentorshipCreate(BaseModel):
    """Request body for creating a mentorship request."""

    mentor_id: UUID


class MentorshipResponse(BaseModel):
    """Mentorship returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mentor_id: UUID
    mentee_id: UUID
    status: MentorshipStatus
    created_at: datetime
    updated_at: datetime
    mentor: UserBrief | None = None
    mentee: UserBrief | None = None


class MentorshipListResponse(BaseModel):
    """List of mentorships."""

    mentorships: list[MentorshipResponse]
