#!/usr/bin/env python
"""Quick test script to verify recommendations work.

Usage:
    cd backend
    uv run python scripts/test_recommendations.py
"""

import asyncio
import os
import sys
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Topic, User
from app.recommender.search import recommend_mentors


async def test_recommendations(session: AsyncSession) -> None:
    """Test the recommend_mentors function."""
    # Get a test user (we'll use the first one as the "requesting" user)
    result = await session.execute(select(User).limit(1))
    requesting_user = result.scalar_one_or_none()

    if not requesting_user:
        print("ERROR: No users found. Run seed_test_mentors.py first.")
        return

    print(f"Requesting user: {requesting_user.email}")
    print()

    # Test recommendations for different topics
    topics_to_test = ["Python", "TypeScript", "UX Design", "Leadership"]

    for topic_name in topics_to_test:
        topic_result = await session.execute(
            select(Topic).where(Topic.name == topic_name)
        )
        topic = topic_result.scalar_one_or_none()

        if not topic:
            print(f"Topic '{topic_name}' not found, skipping...")
            continue

        print(f"--- Recommendations for: {topic_name} ---")

        recommendations = await recommend_mentors(
            db=session,
            user_id=requesting_user.id,
            topic_id=topic.id,
            limit=5,
        )

        if not recommendations:
            print("  No recommendations found.")
        else:
            for i, (mentor_user_id, score) in enumerate(recommendations, 1):
                # Get mentor details
                mentor_result = await session.execute(
                    select(User).where(User.id == mentor_user_id)
                )
                mentor = mentor_result.scalar_one()
                print(f"  {i}. {mentor.display_name} (score: {score:.3f})")

        print()


async def main() -> None:
    """Main entry point."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://skillswap:skillswap_dev_123@localhost:5432/skillswap",
    )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Recommendations Test Script")
    print("=" * 40)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    print()

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        await test_recommendations(session)

    await engine.dispose()
    print("Test complete.")


if __name__ == "__main__":
    asyncio.run(main())
