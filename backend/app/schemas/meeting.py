from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.validators import MeetingURLValidationError, validate_meeting_url
from app.db.models.meeting import MeetingStatus
from app.schemas.mentorship import UserBrief


class MeetingSchedule(BaseModel):
    """Request body for scheduling a meeting."""

    scheduled_time: datetime
    meeting_url: str

    @field_validator("meeting_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        try:
            return validate_meeting_url(v)
        except MeetingURLValidationError as e:
            raise ValueError(str(e)) from e


class MeetingResponse(BaseModel):
    """Meeting returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mentorship_id: UUID
    scheduled_time: datetime | None = None
    meeting_url: str | None = None
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime


class MeetingWithUsersResponse(BaseModel):
    """Meeting with mentor/mentee info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mentorship_id: UUID
    scheduled_time: datetime | None = None
    meeting_url: str | None = None
    status: MeetingStatus
    created_at: datetime
    updated_at: datetime
    mentor: UserBrief | None = None
    mentee: UserBrief | None = None


class MeetingListResponse(BaseModel):
    """List of meetings."""

    meetings: list[MeetingWithUsersResponse]
