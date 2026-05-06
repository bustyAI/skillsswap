"""Async database session management.

This module provides the async session factory for database operations.
All database access should go through sessions created by this factory.

Usage in FastAPI dependencies:
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

Usage in tests:
    async with async_session_factory() as session:
        # do stuff
        await session.commit()
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

# Create the async engine
# - pool_pre_ping=True: Tests connections before using them (handles stale connections)
# - echo=False: Set to True to see all SQL queries in logs (useful for debugging)
engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    echo=False,
)

# Session factory - creates new database sessions
# - expire_on_commit=False: Objects remain usable after commit (important for async)
# - class_=AsyncSession: Use async sessions for FastAPI compatibility
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
