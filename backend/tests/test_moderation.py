"""Tests for moderation endpoints and services.

Tests cover:
- Report creation by any authenticated user
- Admin-only access to report queue
- Admin resolving/dismissing reports with audit logging
- Admin banning users with audit logging
- Admin disabling/enabling mentors with audit logging
- 403 responses for non-admin access attempts
"""

from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditAction, AuditLog
from app.db.models.mentor_profile import MentorProfile
from app.db.models.report import ReportStatus
from app.db.models.user import User
from app.services.moderation_service import (
    MentorProfileNotFoundError,
    UserAlreadyBannedError,
    UserNotFoundError,
    ban_user,
    disable_mentor,
)
from app.services.report_service import (
    InvalidReportTargetError,
    ReportAlreadyResolvedError,
    create_report,
    list_reports_for_admin,
    resolve_report,
)


class TestReportService:
    """Tests for report service functions."""

    async def test_create_report_with_user_target(
        self, async_session: AsyncSession
    ) -> None:
        """User can file a report targeting another user."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="target@test.com")
        async_session.add_all([reporter, target])
        await async_session.commit()

        report = await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="This user is behaving inappropriately.",
            reported_user_id=target.id,
        )

        assert report.reporter_id == reporter.id
        assert report.reported_user_id == target.id
        assert report.status == ReportStatus.PENDING
        assert report.reason == "This user is behaving inappropriately."

    async def test_create_report_requires_target(
        self, async_session: AsyncSession
    ) -> None:
        """Report creation fails without a target."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter2@test.com")
        async_session.add(reporter)
        await async_session.commit()

        with pytest.raises(InvalidReportTargetError):
            await create_report(
                async_session,
                reporter_id=reporter.id,
                reason="No target specified.",
            )

    async def test_list_reports_for_admin(self, async_session: AsyncSession) -> None:
        """Admin can list all reports."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter3@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="target3@test.com")
        async_session.add_all([reporter, target])
        await async_session.commit()

        await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="First report.",
            reported_user_id=target.id,
        )
        await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="Second report.",
            reported_user_id=target.id,
        )

        reports, total = await list_reports_for_admin(async_session)

        assert total >= 2
        assert len(reports) >= 2

    async def test_resolve_report(self, async_session: AsyncSession) -> None:
        """Admin can resolve a report."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter4@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="target4@test.com")
        admin = User(cognito_sub=f"sub-{uuid4()}", email="admin4@test.com")
        async_session.add_all([reporter, target, admin])
        await async_session.commit()

        report = await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="Bad behavior.",
            reported_user_id=target.id,
        )

        resolved = await resolve_report(
            async_session,
            report=report,
            admin_id=admin.id,
            resolution_notes="Warned the user.",
        )

        assert resolved.status == ReportStatus.RESOLVED
        assert resolved.resolution_notes == "Warned the user."
        assert resolved.resolved_by_id == admin.id
        assert resolved.resolved_at is not None

    async def test_dismiss_report(self, async_session: AsyncSession) -> None:
        """Admin can dismiss a report."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter5@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="target5@test.com")
        admin = User(cognito_sub=f"sub-{uuid4()}", email="admin5@test.com")
        async_session.add_all([reporter, target, admin])
        await async_session.commit()

        report = await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="False report.",
            reported_user_id=target.id,
        )

        dismissed = await resolve_report(
            async_session,
            report=report,
            admin_id=admin.id,
            resolution_notes="No violation found.",
            dismiss=True,
        )

        assert dismissed.status == ReportStatus.DISMISSED

    async def test_cannot_resolve_already_resolved_report(
        self, async_session: AsyncSession
    ) -> None:
        """Cannot resolve a report that's already resolved."""
        reporter = User(cognito_sub=f"sub-{uuid4()}", email="reporter6@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="target6@test.com")
        admin = User(cognito_sub=f"sub-{uuid4()}", email="admin6@test.com")
        async_session.add_all([reporter, target, admin])
        await async_session.commit()

        report = await create_report(
            async_session,
            reporter_id=reporter.id,
            reason="Already handled.",
            reported_user_id=target.id,
        )

        await resolve_report(
            async_session,
            report=report,
            admin_id=admin.id,
            resolution_notes="First resolution.",
        )

        with pytest.raises(ReportAlreadyResolvedError):
            await resolve_report(
                async_session,
                report=report,
                admin_id=admin.id,
                resolution_notes="Second resolution.",
            )


class TestModerationService:
    """Tests for moderation service functions."""

    async def test_ban_user(self, async_session: AsyncSession) -> None:
        """Admin can ban a user."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="ban_admin@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="ban_target@test.com")
        async_session.add_all([admin, target])
        await async_session.commit()

        banned = await ban_user(
            async_session,
            admin_id=admin.id,
            target_user_id=target.id,
            reason="Violation of terms.",
        )

        assert banned.banned_at is not None
        assert banned.deleted_at is not None

        result = await async_session.execute(
            select(AuditLog).where(AuditLog.target_user_id == target.id)
        )
        audit = result.scalar_one()
        assert audit.action == AuditAction.BAN_USER
        assert audit.admin_id == admin.id

    async def test_ban_user_not_found(self, async_session: AsyncSession) -> None:
        """Banning non-existent user raises error."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="ban_admin2@test.com")
        async_session.add(admin)
        await async_session.commit()

        with pytest.raises(UserNotFoundError):
            await ban_user(
                async_session,
                admin_id=admin.id,
                target_user_id=uuid4(),
                reason="Does not exist.",
            )

    async def test_ban_already_banned_user(self, async_session: AsyncSession) -> None:
        """Cannot ban already banned user."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="ban_admin3@test.com")
        target = User(cognito_sub=f"sub-{uuid4()}", email="ban_target3@test.com")
        async_session.add_all([admin, target])
        await async_session.commit()

        await ban_user(
            async_session,
            admin_id=admin.id,
            target_user_id=target.id,
            reason="First ban.",
        )

        with pytest.raises(UserAlreadyBannedError):
            await ban_user(
                async_session,
                admin_id=admin.id,
                target_user_id=target.id,
                reason="Second ban.",
            )

    async def test_disable_mentor(self, async_session: AsyncSession) -> None:
        """Admin can disable a mentor profile."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="disable_admin@test.com")
        mentor_user = User(
            cognito_sub=f"sub-{uuid4()}", email="disable_mentor@test.com"
        )
        async_session.add_all([admin, mentor_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        disabled = await disable_mentor(
            async_session,
            admin_id=admin.id,
            target_user_id=mentor_user.id,
            reason="Policy violation.",
        )

        assert disabled.is_enabled is False

        result = await async_session.execute(
            select(AuditLog).where(AuditLog.target_user_id == mentor_user.id)
        )
        audit = result.scalar_one()
        assert audit.action == AuditAction.DISABLE_MENTOR

    async def test_enable_mentor(self, async_session: AsyncSession) -> None:
        """Admin can re-enable a disabled mentor profile (toggle behavior)."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="enable_admin@test.com")
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="enable_mentor@test.com")
        async_session.add_all([admin, mentor_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=False)
        async_session.add(mentor_profile)
        await async_session.commit()

        enabled = await disable_mentor(
            async_session,
            admin_id=admin.id,
            target_user_id=mentor_user.id,
            reason="Appealed successfully.",
        )

        assert enabled.is_enabled is True

        result = await async_session.execute(
            select(AuditLog).where(AuditLog.target_user_id == mentor_user.id)
        )
        audit = result.scalar_one()
        assert audit.action == AuditAction.ENABLE_MENTOR

    async def test_disable_mentor_not_found(self, async_session: AsyncSession) -> None:
        """Disabling non-existent mentor raises error."""
        admin = User(cognito_sub=f"sub-{uuid4()}", email="disable_admin2@test.com")
        async_session.add(admin)
        await async_session.commit()

        with pytest.raises(MentorProfileNotFoundError):
            await disable_mentor(
                async_session,
                admin_id=admin.id,
                target_user_id=uuid4(),
                reason="Does not exist.",
            )


class TestAdminEndpoints403:
    """Tests for 403 responses on admin endpoints for non-admin users."""

    def test_admin_reports_requires_admin(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """GET /api/admin/reports returns 403 for non-admin user."""
        token = make_token(sub="regular-user-sub")

        response = client.get(
            "/api/admin/reports",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_resolve_report_requires_admin(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """POST /api/admin/reports/{id}/resolve returns 403 for non-admin user."""
        token = make_token(sub="regular-user-sub")
        fake_report_id = str(uuid4())

        response = client.post(
            f"/api/admin/reports/{fake_report_id}/resolve",
            headers={"Authorization": f"Bearer {token}"},
            json={"resolution_notes": "test"},
        )

        assert response.status_code == 403

    def test_ban_user_requires_admin(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """POST /api/admin/users/{id}/ban returns 403 for non-admin user."""
        token = make_token(sub="regular-user-sub")
        fake_user_id = str(uuid4())

        response = client.post(
            f"/api/admin/users/{fake_user_id}/ban",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "test"},
        )

        assert response.status_code == 403

    def test_disable_mentor_requires_admin(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """POST /api/admin/mentors/{id}/disable returns 403 for non-admin user."""
        token = make_token(sub="regular-user-sub")
        fake_user_id = str(uuid4())

        response = client.post(
            f"/api/admin/mentors/{fake_user_id}/disable",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "test"},
        )

        assert response.status_code == 403


class TestReportEndpoint:
    """Tests for public report filing endpoint."""

    def test_authenticated_user_can_file_report(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """POST /api/reports creates a report for authenticated user."""
        token = make_token(sub="reporting-user-sub")
        target_user_id = str(uuid4())

        response = client.post(
            "/api/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reported_user_id": target_user_id,
                "reason": "This is a test report with sufficient length.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["reported_user_id"] == target_user_id

    def test_report_requires_target(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """POST /api/reports fails without a target."""
        token = make_token(sub="reporting-user-sub2")

        response = client.post(
            "/api/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reason": "No target specified in this report.",
            },
        )

        assert response.status_code == 400

    def test_report_requires_auth(
        self,
        client: TestClient,
    ) -> None:
        """POST /api/reports requires authentication."""
        response = client.post(
            "/api/reports",
            json={
                "reported_user_id": str(uuid4()),
                "reason": "Anonymous report should fail.",
            },
        )

        assert response.status_code in (401, 403)
