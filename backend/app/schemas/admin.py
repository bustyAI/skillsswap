from pydantic import BaseModel, Field


class BanUserRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class DisableMentorRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class AdminActionResponse(BaseModel):
    success: bool
    message: str
