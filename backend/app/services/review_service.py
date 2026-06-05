from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.mentorship import Mentorship
from app.db.models.review import Review
from app.db.models.user import User

EDIT_WINDOW_DAYS = 7


class ReviewError(Exception):
    pass


class MeetingNotCompletedError(ReviewError):
    pass


class OnlyMenteeCanReviewError(ReviewError):
    pass


class ReviewAlreadyExistsError(ReviewError):
    pass


class ReviewNotFoundError(ReviewError):
    pass


class ReviewEditWindowExpiredError(ReviewError):
    pass


async def get_review_by_meeting_id(
    db: AsyncSession,
    meeting_id: UUID,
) -> Review | None:
    result = await db.execute(
        select(Review)
        .where(Review.meeting_id == meeting_id)
        .options(selectinload(Review.reviewer))
    )
    return result.scalar_one_or_none()


async def create_review(
    db: AsyncSession,
    meeting: Meeting,
    user: User,
    rating: int,
    comment: str | None = None,
) -> Review:
    if meeting.status != MeetingStatus.COMPLETED:
        raise MeetingNotCompletedError(
            f"Cannot review a {meeting.status.value} meeting"
        )

    mentorship = meeting.mentorship
    if user.id != mentorship.mentee_id:
        raise OnlyMenteeCanReviewError("Only the mentee can review a meeting")

    existing = await get_review_by_meeting_id(db, meeting.id)
    if existing is not None:
        raise ReviewAlreadyExistsError("Review already exists for this meeting")

    now = datetime.now(UTC)
    editable_until = now + timedelta(days=EDIT_WINDOW_DAYS)

    review = Review(
        meeting_id=meeting.id,
        reviewer_id=user.id,
        rating=rating,
        comment=comment,
        editable_until=editable_until,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    result = await db.execute(
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.reviewer))
    )
    return result.scalar_one()


async def update_review(
    db: AsyncSession,
    review: Review,
    user: User,
    rating: int | None = None,
    comment: str | None = None,
) -> Review:
    if user.id != review.reviewer_id:
        raise OnlyMenteeCanReviewError("Only the reviewer can edit this review")

    now = datetime.now(UTC)
    if now > review.editable_until:
        raise ReviewEditWindowExpiredError("Edit window has expired for this review")

    if rating is not None:
        review.rating = rating
    if comment is not None:
        review.comment = comment

    await db.commit()
    await db.refresh(review)

    result = await db.execute(
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.reviewer))
    )
    return result.scalar_one()


async def list_mentor_reviews(
    db: AsyncSession,
    mentor_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Review], int]:
    base_query = (
        select(Review)
        .join(Meeting, Review.meeting_id == Meeting.id)
        .join(Mentorship, Meeting.mentorship_id == Mentorship.id)
        .where(Mentorship.mentor_id == mentor_id)
    )

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.options(selectinload(Review.reviewer))
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reviews = list(result.scalars().all())

    return reviews, total
