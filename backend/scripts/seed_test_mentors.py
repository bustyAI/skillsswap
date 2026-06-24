#!/usr/bin/env python
"""Seed test mentors for local development and testing.

Creates fake users with mentor profiles and topic assignments,
then generates embeddings so the recommendations endpoint works.

Usage:
    cd backend
    uv run python scripts/seed_test_mentors.py
"""

import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import MentorProfile, MentorTopic, Topic, User
from app.services.embedding_service import generate_mentor_embedding

# Test mentor data
TEST_MENTORS = [
    {
        "email": "alice.python@example.com",
        "display_name": "Alice Chen",
        "bio": "Senior Python developer with 10 years experience. I specialize in FastAPI, Django, and data engineering. Love helping newcomers learn clean code practices.",
        "headline": "Senior Python Developer & Educator",
        "topics": ["Python", "Data Analysis"],
        "rating_avg": Decimal("4.80"),
        "rating_count": 12,
        "days_since_active": 1,
    },
    {
        "email": "bob.fullstack@example.com",
        "display_name": "Bob Martinez",
        "bio": "Full-stack developer focusing on TypeScript and React. Built apps at startups and Fortune 500 companies. Here to share practical industry knowledge.",
        "headline": "Full-Stack TypeScript Expert",
        "topics": ["TypeScript", "JavaScript"],
        "rating_avg": Decimal("4.65"),
        "rating_count": 8,
        "days_since_active": 3,
    },
    {
        "email": "carol.design@example.com",
        "display_name": "Carol Johnson",
        "bio": "UX designer with background in psychology. I help developers understand user-centered design and build intuitive interfaces.",
        "headline": "UX Designer & Design Thinking Coach",
        "topics": ["UX Design", "UI Design", "Figma"],
        "rating_avg": Decimal("4.90"),
        "rating_count": 15,
        "days_since_active": 0,
    },
    {
        "email": "david.rust@example.com",
        "display_name": "David Kim",
        "bio": "Systems programmer working on high-performance Rust applications. Former C++ developer who found Rust's safety guarantees transformative.",
        "headline": "Rust Systems Programmer",
        "topics": ["Rust", "C++"],
        "rating_avg": Decimal("4.50"),
        "rating_count": 5,
        "days_since_active": 7,
    },
    {
        "email": "eva.leader@example.com",
        "display_name": "Eva Williams",
        "bio": "Engineering manager with 15 years in tech. I coach on leadership, career growth, and navigating corporate environments.",
        "headline": "Engineering Leadership Coach",
        "topics": ["Leadership", "Career Development", "Project Management"],
        "rating_avg": Decimal("4.75"),
        "rating_count": 20,
        "days_since_active": 2,
    },
    {
        "email": "frank.startup@example.com",
        "display_name": "Frank Lopez",
        "bio": "3x startup founder. One exit, two failures. Happy to share lessons learned about building products and raising funding.",
        "headline": "Startup Founder & Advisor",
        "topics": ["Entrepreneurship", "Marketing", "Finance"],
        "rating_avg": Decimal("4.40"),
        "rating_count": 6,
        "days_since_active": 5,
    },
    {
        "email": "grace.java@example.com",
        "display_name": "Grace Park",
        "bio": "Backend engineer specializing in Java and Kotlin. Enterprise experience with microservices and distributed systems.",
        "headline": "Java/Kotlin Backend Specialist",
        "topics": ["Java", "Kotlin"],
        "rating_avg": Decimal("4.60"),
        "rating_count": 9,
        "days_since_active": 4,
    },
    {
        "email": "henry.go@example.com",
        "display_name": "Henry Thompson",
        "bio": "Go developer building cloud-native applications. Previously at Google. Passionate about simplicity and performance.",
        "headline": "Go & Cloud-Native Expert",
        "topics": ["Go", "Python"],
        "rating_avg": Decimal("4.85"),
        "rating_count": 11,
        "days_since_active": 1,
    },
]


async def seed_test_mentors(session: AsyncSession) -> int:
    """Create test mentors with profiles and topic assignments."""
    # Load all topics into a dict for quick lookup
    result = await session.execute(select(Topic))
    topics = {t.name: t for t in result.scalars().all()}

    count = 0
    for mentor_data in TEST_MENTORS:
        # Check if user already exists
        existing = await session.execute(
            select(User).where(User.email == mentor_data["email"])
        )
        if existing.scalar_one_or_none():
            print(f"  Skipping {mentor_data['email']} (already exists)")
            continue

        # Create user
        user = User(
            cognito_sub=f"test-{uuid.uuid4()}",
            email=mentor_data["email"],
            display_name=mentor_data["display_name"],
        )
        session.add(user)
        await session.flush()

        # Create mentor profile
        last_active = datetime.now(UTC) - timedelta(days=mentor_data["days_since_active"])
        profile = MentorProfile(
            user_id=user.id,
            bio=mentor_data["bio"],
            headline=mentor_data["headline"],
            is_enabled=True,
            rating_avg=mentor_data["rating_avg"],
            rating_count=mentor_data["rating_count"],
            last_active_at=last_active,
        )
        session.add(profile)
        await session.flush()

        # Assign topics
        for topic_name in mentor_data["topics"]:
            if topic_name in topics:
                mentor_topic = MentorTopic(
                    mentor_profile_id=profile.id,
                    topic_id=topics[topic_name].id,
                )
                session.add(mentor_topic)

        await session.flush()

        # Generate embedding
        await generate_mentor_embedding(session, profile.id)

        count += 1
        print(f"  [{count}] {mentor_data['display_name']} ({mentor_data['email']})")

    await session.commit()
    return count


async def main() -> None:
    """Main entry point."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://skillswap:skillswap_dev_123@localhost:5432/skillswap",
    )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Test Mentor Seed Script")
    print("=" * 40)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    print()

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        print("Creating test mentors...")
        count = await seed_test_mentors(session)
        print(f"\nCreated {count} test mentors.")

    await engine.dispose()
    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(main())
