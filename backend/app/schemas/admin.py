from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BanUserRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class DisableMentorRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class AdminActionResponse(BaseModel):
    success: bool
    message: str


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    created_at: datetime
    banned_at: datetime | None
    deleted_at: datetime | None
    has_mentor_profile: bool

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class AdminMentorResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    display_name: str | None
    headline: str | None
    bio: str | None
    is_enabled: bool
    rating_avg: Decimal | None
    rating_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminMentorListResponse(BaseModel):
    mentors: list[AdminMentorResponse]
    total: int
    page: int
    page_size: int
