from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditAction, AuditLog


async def log_admin_action(
    db: AsyncSession,
    admin_id: UUID,
    action: AuditAction,
    target_user_id: UUID | None = None,
    target_report_id: UUID | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Append a record to the audit log. This table is append-only."""
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        target_report_id=target_report_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry
