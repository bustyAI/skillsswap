"""Report endpoints for user-submitted reports."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.dependencies import DbSession
from app.schemas.auth import TokenClaims
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import InvalidReportTargetError, create_report
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def file_report(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    report_data: ReportCreate,
) -> ReportResponse:
    """File a report against a user or mentorship.

    Any authenticated user can file a report. At least one of
    reported_user_id or reported_mentorship_id must be provided.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    try:
        report = await create_report(
            db=db,
            reporter_id=user.id,
            reason=report_data.reason,
            reported_user_id=report_data.reported_user_id,
            reported_mentorship_id=report_data.reported_mentorship_id,
        )
    except InvalidReportTargetError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return ReportResponse.model_validate(report)
