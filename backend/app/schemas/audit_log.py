from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    admin_id: UUID | None
    action: AuditAction
    target_user_id: UUID | None
    target_report_id: UUID | None
    details: str | None
    created_at: datetime
