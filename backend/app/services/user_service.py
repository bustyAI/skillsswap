"""User service - business logic for user operations."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Get existing user or create new one (just-in-time provisioning)."""
    user = await get_user_by_cognito_sub(db, cognito_sub)
    if user is None:
        user = await create_user(db, cognito_sub, email)
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
