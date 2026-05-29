"""Topic service - business logic for topic discovery."""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentor_topic import MentorTopic
from app.db.models.topic import Topic
from app.db.models.user import User


async def list_topics(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    parent_topic_id: UUID | None = None,
) -> tuple[list[Topic], int]:
    """List topics with optional parent filter and pagination."""
    query = select(Topic)

    if parent_topic_id is not None:
        query = query.where(Topic.parent_topic_id == parent_topic_id)
    else:
        query = query.where(Topic.parent_topic_id.is_(None))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Topic.name).offset(offset).limit(page_size)

    result = await db.execute(query)
    topics = list(result.scalars().all())

    return topics, total


async def get_topic_by_id(db: AsyncSession, topic_id: UUID) -> Topic | None:
    """Get a single topic by ID."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    return result.scalar_one_or_none()


async def get_mentors_for_topic(
    db: AsyncSession,
    topic_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[MentorProfile], int]:
    """Get mentors who have this topic, ordered by rating_avg DESC."""
    base_query = (
        select(MentorProfile)
        .join(MentorTopic, MentorProfile.id == MentorTopic.mentor_profile_id)
        .join(User, MentorProfile.user_id == User.id)
        .where(
            MentorTopic.topic_id == topic_id,
            MentorProfile.is_enabled.is_(True),
            User.deleted_at.is_(None),
        )
    )

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        base_query.order_by(
            MentorProfile.rating_avg.desc().nulls_last(),
            MentorProfile.rating_count.desc(),
        )
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    mentors = list(result.scalars().all())

    return mentors, total


async def search_topics(
    db: AsyncSession,
    query: str,
    limit: int = 10,
) -> list[tuple[Topic, float]]:
    """Search topics by name using trigram similarity."""
    if not query.strip():
        return []

    stmt = (
        select(Topic, func.similarity(Topic.name, query).label("sim"))
        .where(text("name % :query").bindparams(query=query))
        .order_by(text("sim DESC"))
        .limit(limit)
    )

    result = await db.execute(stmt)
    return [(row[0], float(row[1])) for row in result.all()]
