"""Pydantic schemas for Message endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    """Request body for sending a message."""

    content: str = Field(..., min_length=1, max_length=10000)


class SenderBrief(BaseModel):
    """Minimal sender info for message responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None = None
    email: str


class MessageResponse(BaseModel):
    """Message returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    sender_id: UUID | None
    content: str
    is_system: bool
    created_at: datetime
    sender: SenderBrief | None = None


class MessageListResponse(BaseModel):
    """Paginated list of messages with cursor-based pagination."""

    messages: list[MessageResponse]
    next_cursor: str | None = None
    has_more: bool = False
