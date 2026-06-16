"""Embedding service - generates and stores vector embeddings for recommendations."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MentorEmbedding, MentorProfile, MentorTopic, Topic, TopicEmbedding
from app.recommender.embeddings import encode

logger = logging.getLogger(__name__)


async def generate_mentor_embedding(
    db: AsyncSession,
    mentor_profile_id: UUID,
) -> MentorEmbedding | None:
    """Generate and store embedding for a mentor profile.

    Builds text from: bio + ' ' + (space-joined topic names)
    Then encodes to 384-dim vector and upserts into mentor_embedding table.

    Returns None if mentor profile not found.
    """
    profile_result = await db.execute(
        select(MentorProfile).where(MentorProfile.id == mentor_profile_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        logger.warning("Mentor profile %s not found for embedding generation", mentor_profile_id)
        return None

    topics_result = await db.execute(
        select(Topic)
        .join(MentorTopic)
        .where(MentorTopic.mentor_profile_id == mentor_profile_id)
        .order_by(Topic.name)
    )
    topics = list(topics_result.scalars().all())

    text_parts = []
    if profile.bio:
        text_parts.append(profile.bio)
    if profile.headline:
        text_parts.append(profile.headline)
    if topics:
        topic_names = " ".join(t.name for t in topics)
        text_parts.append(topic_names)

    text_to_encode = " ".join(text_parts) if text_parts else ""

    if not text_to_encode.strip():
        logger.info("Mentor profile %s has no text to encode, using placeholder", mentor_profile_id)
        text_to_encode = "mentor"

    embedding_vector = encode(text_to_encode)

    existing_result = await db.execute(
        select(MentorEmbedding).where(MentorEmbedding.mentor_profile_id == mentor_profile_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.embedding = embedding_vector
        mentor_embedding = existing
        logger.info("Updated embedding for mentor profile %s", mentor_profile_id)
    else:
        mentor_embedding = MentorEmbedding(
            mentor_profile_id=mentor_profile_id,
            embedding=embedding_vector,
        )
        db.add(mentor_embedding)
        logger.info("Created embedding for mentor profile %s", mentor_profile_id)

    await db.flush()
    return mentor_embedding


async def generate_topic_embedding(
    db: AsyncSession,
    topic: Topic,
) -> TopicEmbedding:
    """Generate and store embedding for a topic.

    Builds text from: name + ' ' + description
    Then encodes to 384-dim vector and upserts into topic_embedding table.
    """
    text_parts = [topic.name]
    if topic.description:
        text_parts.append(topic.description)

    text_to_encode = " ".join(text_parts)
    embedding_vector = encode(text_to_encode)

    existing_result = await db.execute(
        select(TopicEmbedding).where(TopicEmbedding.topic_id == topic.id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.embedding = embedding_vector
        topic_embedding = existing
        logger.info("Updated embedding for topic %s", topic.name)
    else:
        topic_embedding = TopicEmbedding(
            topic_id=topic.id,
            embedding=embedding_vector,
        )
        db.add(topic_embedding)
        logger.info("Created embedding for topic %s", topic.name)

    await db.flush()
    return topic_embedding
