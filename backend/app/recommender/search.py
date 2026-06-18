"""Vector search and ranking for mentor recommendations."""

import math
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.block import Block
from app.db.models.mentor_embedding import MentorEmbedding
from app.db.models.mentor_profile import MentorProfile
from app.db.models.report import Report, ReportStatus
from app.db.models.topic_embedding import TopicEmbedding
from app.db.models.user import User


def _compute_activity_recency(last_active_at: datetime | None) -> float:
    """Compute activity recency score using exponential decay.

    Returns exp(-days_since_last_active / 30).
    If last_active_at is None, returns 0.5 as default.
    """
    if last_active_at is None:
        return 0.5

    now = datetime.now(UTC)
    if last_active_at.tzinfo is None:
        last_active_at = last_active_at.replace(tzinfo=UTC)

    days_since = (now - last_active_at).total_seconds() / 86400
    return math.exp(-days_since / 30)


def _compute_normalized_rating(
    rating_avg: Decimal | None,
    rating_count: int,
) -> float:
    """Compute normalized rating score.

    Returns rating_avg / 5.0.
    If rating_count < 3, returns 0.5 (not enough data for confidence).
    """
    if rating_count < 3 or rating_avg is None:
        return 0.5

    return float(rating_avg) / 5.0


def _compute_moderation_penalty(open_reports_count: int) -> float:
    """Compute moderation penalty based on open reports.

    Returns min(1.0, open_reports_count / 10).
    """
    return min(1.0, open_reports_count / 10)


async def recommend_mentors(
    db: AsyncSession,
    user_id: UUID,
    topic_id: UUID,
    limit: int = 20,
) -> list[tuple[UUID, float]]:
    """Recommend mentors for a topic, ranked by relevance and quality.

    Returns list of (mentor_user_id, score) tuples sorted by score descending.
    Returns empty list if topic has no embedding or no matching mentors.
    """
    # 1. Load topic embedding as query vector
    topic_emb_result = await db.execute(
        select(TopicEmbedding.embedding).where(TopicEmbedding.topic_id == topic_id)
    )
    topic_embedding = topic_emb_result.scalar_one_or_none()
    if topic_embedding is None:
        return []

    # 2. Get blocked user IDs (both directions)
    blocked_by_user = select(Block.blocked_id).where(Block.blocker_id == user_id)
    blocking_user = select(Block.blocker_id).where(Block.blocked_id == user_id)

    # 3. Cosine similarity search against mentor_embedding
    #    pgvector <=> returns cosine distance, so similarity = 1 - distance
    cosine_distance = MentorEmbedding.embedding.cosine_distance(topic_embedding)

    candidates_query = (
        select(
            MentorEmbedding.mentor_profile_id,
            cosine_distance.label("distance"),
        )
        .order_by(cosine_distance)
        .limit(100)
    )
    candidates_result = await db.execute(candidates_query)
    candidates = candidates_result.all()

    if not candidates:
        return []

    mentor_profile_ids = [c.mentor_profile_id for c in candidates]
    distance_by_profile = {c.mentor_profile_id: c.distance for c in candidates}

    # 4. Fetch mentor profiles with user data, applying filters
    profiles_query = (
        select(MentorProfile)
        .join(User, MentorProfile.user_id == User.id)
        .where(
            MentorProfile.id.in_(mentor_profile_ids),
            MentorProfile.is_enabled.is_(True),
            User.deleted_at.is_(None),
            User.banned_at.is_(None),
            User.id != user_id,
            User.id.not_in(blocked_by_user),
            User.id.not_in(blocking_user),
        )
    )
    profiles_result = await db.execute(profiles_query)
    profiles = list(profiles_result.scalars().all())

    if not profiles:
        return []

    # 5. Fetch open reports count per mentor user
    open_statuses = [ReportStatus.PENDING, ReportStatus.UNDER_REVIEW]
    mentor_user_ids = [p.user_id for p in profiles]

    reports_query = (
        select(
            Report.reported_user_id,
            func.count(Report.id).label("report_count"),
        )
        .where(
            Report.reported_user_id.in_(mentor_user_ids),
            Report.status.in_(open_statuses),
        )
        .group_by(Report.reported_user_id)
    )
    reports_result = await db.execute(reports_query)
    reports_by_user: dict[UUID, int] = {
        row.reported_user_id: row.report_count for row in reports_result.all()
    }

    # 6. Compute final scores
    scored_mentors: list[tuple[UUID, float]] = []

    for profile in profiles:
        distance = distance_by_profile[profile.id]
        similarity = 1.0 - float(distance)

        recency = _compute_activity_recency(profile.last_active_at)
        norm_rating = _compute_normalized_rating(
            profile.rating_avg, profile.rating_count
        )
        open_reports = reports_by_user.get(profile.user_id, 0)
        penalty = _compute_moderation_penalty(open_reports)

        final_score = (
            0.60 * similarity + 0.20 * norm_rating + 0.15 * recency - 0.05 * penalty
        )

        scored_mentors.append((profile.user_id, final_score))

    # 7. Sort by score descending and return top N
    scored_mentors.sort(key=lambda x: x[1], reverse=True)
    return scored_mentors[:limit]
