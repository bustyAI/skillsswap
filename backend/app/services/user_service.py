"""User service - business logic for user operations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.mentor_profile import MentorProfile
from app.db.models.user import User
from app.schemas.user import UserUpdate


async def get_user_by_cognito_sub(
    db: AsyncSession,
    cognito_sub: str,
) -> User | None:
    result = await db.execute(
        select(User).where(
            User.cognito_sub == cognito_sub,
            User.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    cognito_sub: str,
    email: str,
) -> User:
    user = User(
        cognito_sub=cognito_sub,
        email=email,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user(
    db: AsyncSession,
    cognito_sub: str,
    email: str,
) -> User:
    """Get existing user or create new one (just-in-time provisioning).

    Also updates email if it changed (handles migration from old token format).
    """
    user = await get_user_by_cognito_sub(db, cognito_sub)
    if user is None:
        user = await create_user(db, cognito_sub, email)
        user.email = email
    elif user.email != email:
        await db.commit()
        await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    updates: UserUpdate,
) -> User:
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def soft_delete_user(
    db: AsyncSession,
    user: User,
) -> None:
    """Soft-delete user with cascade.

    V1 cascade behavior:
    - Sets user.deleted_at
    - Disables mentor_profile if it exists (is_enabled = False)
    """
    user.deleted_at = datetime.now(UTC)

    result = await db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user.id)
    )
    mentor_profile = result.scalar_one_or_none()
    if mentor_profile is not None:
        mentor_profile.is_enabled = False

    await db.commit()


async def search_users_by_email(
    db: AsyncSession,
    email_query: str,
    page: int = 1,
    page_size: int = 20,
    include_banned: bool = True,
) -> tuple[list[User], int]:
    """Search users by email (case-insensitive partial match)."""
    base_query = select(User).options(joinedload(User.mentor_profile))

    if not include_banned:
        base_query = base_query.where(User.banned_at.is_(None))

    search_filter = User.email.ilike(f"%{email_query}%")
    filtered_query = base_query.where(search_filter)

    count_query = select(func.count(User.id)).where(search_filter)
    if not include_banned:
        count_query = count_query.where(User.banned_at.is_(None))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    paginated_query = (
        filtered_query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await db.execute(paginated_query)
    users = list(result.scalars().unique().all())

    return users, total


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_mentors_for_admin(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    enabled_only: bool = False,
) -> tuple[list[MentorProfile], int]:
    """List all mentor profiles with user info for admin view."""
    base_query = select(MentorProfile).options(joinedload(MentorProfile.user))

    if enabled_only:
        base_query = base_query.where(MentorProfile.is_enabled.is_(True))

    count_query = select(func.count(MentorProfile.id))
    if enabled_only:
        count_query = count_query.where(MentorProfile.is_enabled.is_(True))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    paginated_query = (
        base_query.order_by(MentorProfile.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(paginated_query)
    mentors = list(result.scalars().unique().all())

    return mentors, total
