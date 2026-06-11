from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditAction
from app.db.models.mentor_profile import MentorProfile
from app.db.models.user import User
from app.services.audit_log_service import log_admin_action


class ModerationError(Exception):
    pass


class UserNotFoundError(ModerationError):
    pass


class UserAlreadyBannedError(ModerationError):
    pass


class MentorProfileNotFoundError(ModerationError):
    pass


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
    include_deleted: bool = False,
) -> User | None:
    query = select(User).where(User.id == user_id)
    if not include_deleted:
        query = query.where(User.deleted_at.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_mentor_profile_by_user_id(
    db: AsyncSession,
    user_id: UUID,
) -> MentorProfile | None:
    result = await db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def ban_user(
    db: AsyncSession,
    admin_id: UUID,
    target_user_id: UUID,
    reason: str,
    ip_address: str | None = None,
) -> User:
    # First check if user exists at all (including deleted/banned)
    user = await get_user_by_id(db, target_user_id, include_deleted=True)
    if user is None:
        raise UserNotFoundError(f"User {target_user_id} not found")

    if user.banned_at is not None:
        raise UserAlreadyBannedError(f"User {target_user_id} is already banned")

    # Also check if user was soft-deleted (but not banned)
    if user.deleted_at is not None and user.banned_at is None:
        raise UserNotFoundError(f"User {target_user_id} not found")

    now = datetime.now(UTC)
    user.banned_at = now
    user.deleted_at = now

    mentor_profile = await get_mentor_profile_by_user_id(db, target_user_id)
    if mentor_profile is not None:
        mentor_profile.is_enabled = False

    await log_admin_action(
        db,
        admin_id=admin_id,
        action=AuditAction.BAN_USER,
        target_user_id=target_user_id,
        details=reason,
        ip_address=ip_address,
    )

    await db.commit()
    await db.refresh(user)
    return user


async def disable_mentor(
    db: AsyncSession,
    admin_id: UUID,
    target_user_id: UUID,
    reason: str,
    ip_address: str | None = None,
) -> MentorProfile:
    mentor_profile = await get_mentor_profile_by_user_id(db, target_user_id)
    if mentor_profile is None:
        raise MentorProfileNotFoundError(
            f"Mentor profile for user {target_user_id} not found"
        )

    new_state = not mentor_profile.is_enabled
    mentor_profile.is_enabled = new_state

    action = AuditAction.ENABLE_MENTOR if new_state else AuditAction.DISABLE_MENTOR

    await log_admin_action(
        db,
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        details=reason,
        ip_address=ip_address,
    )

    await db.commit()
    await db.refresh(mentor_profile)
    return mentor_profile
