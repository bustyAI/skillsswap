"""Database dependencies for FastAPI.

This module provides FastAPI dependencies for database access.
Use these in route handlers to get database sessions.

Example:
    @router.get("/users/{user_id}")
    async def get_user(
        user_id: UUID,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> UserResponse:
        # db is now an async database session
        user = await db.get(User, user_id)
        ...
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for a request.

    This is a FastAPI dependency that creates a new database session
    for each request and automatically closes it when the request ends.

    The session is yielded (not returned) so FastAPI can clean it up
    after the response is sent, even if an exception occurs.

    Yields:
        AsyncSession: A SQLAlchemy async session connected to the database.

    Example:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        yield session


# Type alias for cleaner dependency injection in route handlers
# Instead of: db: AsyncSession = Depends(get_db)
# You write:  db: DbSession
DbSession = Annotated[AsyncSession, Depends(get_db)]
