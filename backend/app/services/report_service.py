from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.report import Report, ReportStatus


class ReportError(Exception):
    pass


class ReportNotFoundError(ReportError):
    pass


class ReportAlreadyResolvedError(ReportError):
    pass


class InvalidReportTargetError(ReportError):
    pass


async def create_report(
    db: AsyncSession,
    reporter_id: UUID,
    reason: str,
    reported_user_id: UUID | None = None,
    reported_mentorship_id: UUID | None = None,
) -> Report:
    if reported_user_id is None and reported_mentorship_id is None:
        raise InvalidReportTargetError(
            "At least one of reported_user_id or reported_mentorship_id must be provided"
        )

    report = Report(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        reported_mentorship_id=reported_mentorship_id,
        reason=reason,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_report_by_id(
    db: AsyncSession,
    report_id: UUID,
) -> Report | None:
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.reporter),
            selectinload(Report.reported_user),
            selectinload(Report.resolved_by),
        )
    )
    return result.scalar_one_or_none()


async def list_reports_for_admin(
    db: AsyncSession,
    status_filter: ReportStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Report], int]:
    base_query = select(Report)

    if status_filter is not None:
        base_query = base_query.where(Report.status == status_filter)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.options(
            selectinload(Report.reporter),
            selectinload(Report.reported_user),
            selectinload(Report.resolved_by),
        )
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reports = list(result.scalars().all())

    return reports, total


async def resolve_report(
    db: AsyncSession,
    report: Report,
    admin_id: UUID,
    resolution_notes: str,
    dismiss: bool = False,
) -> Report:
    if report.status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
        raise ReportAlreadyResolvedError(
            f"Report is already {report.status.value.lower()}"
        )

    report.status = ReportStatus.DISMISSED if dismiss else ReportStatus.RESOLVED
    report.resolution_notes = resolution_notes
    report.resolved_by_id = admin_id
    report.resolved_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(report)

    result = await db.execute(
        select(Report)
        .where(Report.id == report.id)
        .options(
            selectinload(Report.reporter),
            selectinload(Report.reported_user),
            selectinload(Report.resolved_by),
        )
    )
    return result.scalar_one()
