"""Admin moderation endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.core.admin import AdminUser
from app.db.dependencies import DbSession
from app.db.models.audit_log import AuditAction
from app.db.models.report import ReportStatus
from app.schemas.admin import (
    AdminActionResponse,
    AdminMentorListResponse,
    AdminMentorResponse,
    AdminUserListResponse,
    AdminUserResponse,
    BanUserRequest,
    DisableMentorRequest,
)
from app.schemas.report import (
    AdminReportListResponse,
    AdminReportResponse,
    ResolveReportRequest,
)
from app.services.audit_log_service import log_admin_action
from app.services.moderation_service import (
    MentorProfileNotFoundError,
    UserAlreadyBannedError,
    UserNotFoundError,
    ban_user,
    disable_mentor,
)
from app.services.report_service import (
    ReportAlreadyResolvedError,
    get_report_by_id,
    list_reports_for_admin,
    resolve_report,
)
from app.services.user_service import (
    get_user_by_cognito_sub,
    list_mentors_for_admin,
    search_users_by_email,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/reports", response_model=AdminReportListResponse)
async def list_reports(
    admin: AdminUser,
    db: DbSession,
    status_filter: ReportStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AdminReportListResponse:
    """List reports in the moderation queue.

    Optionally filter by status. Returns reports newest first.
    """
    reports, total = await list_reports_for_admin(
        db=db,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )

    return AdminReportListResponse(
        reports=[AdminReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/reports/{report_id}/resolve", response_model=AdminReportResponse)
async def resolve_report_endpoint(
    report_id: UUID,
    admin: AdminUser,
    db: DbSession,
    request: Request,
    resolve_data: ResolveReportRequest,
) -> AdminReportResponse:
    """Resolve or dismiss a report.

    Sets resolution_notes and marks the report as RESOLVED or DISMISSED.
    Writes to the audit log.
    """
    report = await get_report_by_id(db, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    admin_user = await get_user_by_cognito_sub(db, admin.sub)
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin user record not found",
        )

    try:
        resolved = await resolve_report(
            db=db,
            report=report,
            admin_id=admin_user.id,
            resolution_notes=resolve_data.resolution_notes,
            dismiss=resolve_data.dismiss,
        )
    except ReportAlreadyResolvedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    action = (
        AuditAction.DISMISS_REPORT
        if resolve_data.dismiss
        else AuditAction.RESOLVE_REPORT
    )
    await log_admin_action(
        db=db,
        admin_id=admin_user.id,
        action=action,
        target_report_id=report_id,
        details=resolve_data.resolution_notes,
        ip_address=_get_client_ip(request),
    )
    await db.commit()

    return AdminReportResponse.model_validate(resolved)


@router.post("/users/{user_id}/ban", response_model=AdminActionResponse)
async def ban_user_endpoint(
    user_id: UUID,
    admin: AdminUser,
    db: DbSession,
    request: Request,
    ban_data: BanUserRequest,
) -> AdminActionResponse:
    """Ban a user.

    Sets user.banned_at and user.deleted_at, disables mentor profile.
    Writes to the audit log.
    """
    admin_user = await get_user_by_cognito_sub(db, admin.sub)
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin user record not found",
        )

    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban yourself",
        )

    try:
        await ban_user(
            db=db,
            admin_id=admin_user.id,
            target_user_id=user_id,
            reason=ban_data.reason,
            ip_address=_get_client_ip(request),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except UserAlreadyBannedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return AdminActionResponse(
        success=True,
        message=f"User {user_id} has been banned",
    )


@router.post("/mentors/{user_id}/disable", response_model=AdminActionResponse)
async def disable_mentor_endpoint(
    user_id: UUID,
    admin: AdminUser,
    db: DbSession,
    request: Request,
    disable_data: DisableMentorRequest,
) -> AdminActionResponse:
    """Toggle a mentor profile's enabled status.

    If currently enabled, disables it. If disabled, re-enables it.
    Writes to the audit log.
    """
    admin_user = await get_user_by_cognito_sub(db, admin.sub)
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin user record not found",
        )

    try:
        mentor_profile = await disable_mentor(
            db=db,
            admin_id=admin_user.id,
            target_user_id=user_id,
            reason=disable_data.reason,
            ip_address=_get_client_ip(request),
        )
    except MentorProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    action_word = "enabled" if mentor_profile.is_enabled else "disabled"
    return AdminActionResponse(
        success=True,
        message=f"Mentor profile for user {user_id} has been {action_word}",
    )


@router.get("/users/search", response_model=AdminUserListResponse)
async def search_users(
    admin: AdminUser,
    db: DbSession,
    email: str = Query(..., min_length=1, description="Email to search for"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_banned: bool = Query(True, description="Include banned users in results"),
) -> AdminUserListResponse:
    """Search users by email (partial match, case-insensitive)."""
    users, total = await search_users_by_email(
        db=db,
        email_query=email,
        page=page,
        page_size=page_size,
        include_banned=include_banned,
    )

    return AdminUserListResponse(
        users=[
            AdminUserResponse(
                id=u.id,
                email=u.email,
                display_name=u.display_name,
                avatar_url=u.avatar_url,
                created_at=u.created_at,
                banned_at=u.banned_at,
                deleted_at=u.deleted_at,
                has_mentor_profile=u.mentor_profile is not None,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/mentors", response_model=AdminMentorListResponse)
async def list_mentors(
    admin: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enabled_only: bool = Query(False, description="Only show enabled mentors"),
) -> AdminMentorListResponse:
    """List all mentor profiles for admin management."""
    mentors, total = await list_mentors_for_admin(
        db=db,
        page=page,
        page_size=page_size,
        enabled_only=enabled_only,
    )

    return AdminMentorListResponse(
        mentors=[
            AdminMentorResponse(
                id=m.id,
                user_id=m.user_id,
                email=m.user.email,
                display_name=m.user.display_name,
                headline=m.headline,
                bio=m.bio,
                is_enabled=m.is_enabled,
                rating_avg=m.rating_avg,
                rating_count=m.rating_count,
                created_at=m.created_at,
            )
            for m in mentors
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
