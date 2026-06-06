from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.report import ReportStatus


class ReportCreate(BaseModel):
    reported_user_id: UUID | None = None
    reported_mentorship_id: UUID | None = None
    reason: str = Field(..., min_length=10, max_length=5000)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID
    reported_user_id: UUID | None
    reported_mentorship_id: UUID | None
    reason: str
    status: ReportStatus
    created_at: datetime
    updated_at: datetime


class ReporterBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None = None


class ReportedUserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None = None


class ResolverBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None = None


class AdminReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID
    reported_user_id: UUID | None
    reported_mentorship_id: UUID | None
    reason: str
    status: ReportStatus
    resolution_notes: str | None
    resolved_by_id: UUID | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    reporter: ReporterBrief | None = None
    reported_user: ReportedUserBrief | None = None
    resolved_by: ResolverBrief | None = None


class AdminReportListResponse(BaseModel):
    reports: list[AdminReportResponse]
    total: int
    page: int
    page_size: int


class ResolveReportRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=1, max_length=5000)
    dismiss: bool = False
