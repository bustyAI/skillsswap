"""User service - business logic for user operations."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    """V1: Only sets deleted_at. Full cascade is deferred."""
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()
