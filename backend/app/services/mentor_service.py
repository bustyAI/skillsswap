"""Mentor service - business logic for mentor profile operations."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentor_topic import MentorTopic
from app.db.models.topic import Topic
from app.db.models.user import User
from app.schemas.mentor_profile import MentorProfileCreate, MentorProfileUpdate
from app.services.embedding_service import generate_mentor_embedding

logger = logging.getLogger(__name__)


async def get_mentor_profile_by_user_id(
    db: AsyncSession,
    user_id: UUID,
) -> MentorProfile | None:
    """Get a mentor profile by the owning user's ID."""
    result = await db.execute(
        select(MentorProfile)
        .join(User)
        .where(
            MentorProfile.user_id == user_id,
            User.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_mentor_profile(
    db: AsyncSession,
    user: User,
    data: MentorProfileCreate,
) -> MentorProfile:
    """Create a mentor profile for a user.

    Raises IntegrityError if the user already has a mentor profile
    (enforced by UNIQUE constraint on user_id).
    """
    mentor_profile = MentorProfile(
        user_id=user.id,
        bio=data.bio,
        headline=data.headline,
    )
    db.add(mentor_profile)
    await db.commit()
    await db.refresh(mentor_profile)
    await generate_mentor_embedding(db, mentor_profile.id)
    await db.commit()
    return mentor_profile


async def update_mentor_profile(
    db: AsyncSession,
    mentor_profile: MentorProfile,
    data: MentorProfileUpdate,
) -> MentorProfile:
    """Update a mentor profile's fields."""
    update_data = data.model_dump(exclude_unset=True)

    if update_data:
        for field, value in update_data.items():
            setattr(mentor_profile, field, value)
        await db.commit()
        await db.refresh(mentor_profile)
        await generate_mentor_embedding(db, mentor_profile.id)
        await db.commit()

    return mentor_profile


async def get_mentor_topics(
    db: AsyncSession,
    mentor_profile: MentorProfile,
) -> list[Topic]:
    """Get all topics associated with a mentor profile."""
    result = await db.execute(
        select(Topic)
        .join(MentorTopic)
        .where(MentorTopic.mentor_profile_id == mentor_profile.id)
        .order_by(Topic.name)
    )
    return list(result.scalars().all())


async def replace_mentor_topics(
    db: AsyncSession,
    mentor_profile: MentorProfile,
    topic_ids: list[UUID],
) -> list[Topic]:
    """Replace all topics for a mentor profile.

    Deletes existing MentorTopic rows and creates new ones for the given topic_ids.
    Returns the list of Topic objects that were assigned.
    """
    await db.execute(
        select(MentorTopic).where(MentorTopic.mentor_profile_id == mentor_profile.id)
    )
    existing = await db.execute(
        select(MentorTopic).where(MentorTopic.mentor_profile_id == mentor_profile.id)
    )
    for mt in existing.scalars().all():
        await db.delete(mt)

    if not topic_ids:
        await db.commit()
        return []

    topics_result = await db.execute(select(Topic).where(Topic.id.in_(topic_ids)))
    topics = list(topics_result.scalars().all())
    found_ids = {t.id for t in topics}

    for topic_id in topic_ids:
        if topic_id in found_ids:
            mentor_topic = MentorTopic(
                mentor_profile_id=mentor_profile.id,
                topic_id=topic_id,
            )
            db.add(mentor_topic)

    await db.commit()
    await generate_mentor_embedding(db, mentor_profile.id)
    await db.commit()

    return sorted(topics, key=lambda t: t.name)
