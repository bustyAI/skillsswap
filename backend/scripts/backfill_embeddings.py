#!/usr/bin/env python
"""Backfill script for generating embeddings on existing data.

Generates embeddings for all topics and mentor profiles that were created
before embedding generation was wired into the create/update flows.

Usage:
    cd backend
    uv run python scripts/backfill_embeddings.py

This script is idempotent - running it multiple times will update existing
embeddings rather than creating duplicates.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import MentorEmbedding, MentorProfile, Topic, TopicEmbedding
from app.services.embedding_service import (
    generate_mentor_embedding,
    generate_topic_embedding,
)


async def backfill_topic_embeddings(session: AsyncSession) -> int:
    """Generate embeddings for all topics without one."""
    result = await session.execute(select(Topic))
    topics = list(result.scalars().all())

    count = 0
    for topic in topics:
        await generate_topic_embedding(session, topic)
        count += 1
        print(f"  [{count}/{len(topics)}] {topic.name}")

    await session.commit()
    return count


async def backfill_mentor_embeddings(session: AsyncSession) -> int:
    """Generate embeddings for all mentor profiles without one."""
    result = await session.execute(select(MentorProfile))
    profiles = list(result.scalars().all())

    count = 0
    for profile in profiles:
        await generate_mentor_embedding(session, profile.id)
        count += 1
        print(f"  [{count}/{len(profiles)}] Mentor profile {profile.id}")

    await session.commit()
    return count


async def get_counts(session: AsyncSession) -> tuple[int, int, int, int]:
    """Return counts of topics, topic_embeddings, mentor_profiles, mentor_embeddings."""
    topic_count = await session.execute(select(func.count()).select_from(Topic))
    topic_emb_count = await session.execute(
        select(func.count()).select_from(TopicEmbedding)
    )
    mentor_count = await session.execute(
        select(func.count()).select_from(MentorProfile)
    )
    mentor_emb_count = await session.execute(
        select(func.count()).select_from(MentorEmbedding)
    )

    return (
        topic_count.scalar() or 0,
        topic_emb_count.scalar() or 0,
        mentor_count.scalar() or 0,
        mentor_emb_count.scalar() or 0,
    )


async def run_backfill(database_url: str) -> None:
    """Execute the backfill process."""
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        print("Current counts before backfill:")
        t_count, te_count, m_count, me_count = await get_counts(session)
        print(f"  Topics: {t_count}, Topic embeddings: {te_count}")
        print(f"  Mentor profiles: {m_count}, Mentor embeddings: {me_count}")
        print()

        print("Backfilling topic embeddings...")
        topics_processed = await backfill_topic_embeddings(session)
        print(f"Processed {topics_processed} topics.\n")

        print("Backfilling mentor embeddings...")
        mentors_processed = await backfill_mentor_embeddings(session)
        print(f"Processed {mentors_processed} mentor profiles.\n")

        print("Final counts after backfill:")
        t_count, te_count, m_count, me_count = await get_counts(session)
        print(f"  Topics: {t_count}, Topic embeddings: {te_count}")
        print(f"  Mentor profiles: {m_count}, Mentor embeddings: {me_count}")

    await engine.dispose()


async def main() -> None:
    """Main entry point."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://skillswap:skillswap_dev_123@localhost:5432/skillswap",
    )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Embedding Backfill Script")
    print("=" * 40)
    print(
        f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}"
    )
    print()

    await run_backfill(database_url)
    print("\nBackfill complete.")


if __name__ == "__main__":
    asyncio.run(main())
