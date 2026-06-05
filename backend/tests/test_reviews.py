from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.user import User
from app.services.review_service import (
    MeetingNotCompletedError,
    OnlyMenteeCanReviewError,
    ReviewAlreadyExistsError,
    ReviewEditWindowExpiredError,
    create_review,
    list_mentor_reviews,
    update_review,
)


async def create_test_setup(
    async_session: AsyncSession,
) -> tuple[User, User, Mentorship]:
    mentor_user = User(cognito_sub=f"sub-{uuid4()}", email=f"mentor_{uuid4()}@test.com")
    mentee_user = User(cognito_sub=f"sub-{uuid4()}", email=f"mentee_{uuid4()}@test.com")
    async_session.add_all([mentor_user, mentee_user])
    await async_session.commit()

    mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
    async_session.add(mentor_profile)
    await async_session.commit()

    mentorship = Mentorship(
        mentor_id=mentor_user.id,
        mentee_id=mentee_user.id,
        status=MentorshipStatus.ACTIVE,
    )
    async_session.add(mentorship)
    await async_session.commit()
    await async_session.refresh(mentorship)

    return mentor_user, mentee_user, mentorship


async def create_meeting_with_status(
    async_session: AsyncSession,
    mentorship: Mentorship,
    status: MeetingStatus,
) -> Meeting:
    meeting = Meeting(
        mentorship_id=mentorship.id,
        status=status,
        scheduled_time=datetime.now(UTC) - timedelta(hours=1)
        if status in (MeetingStatus.SCHEDULED, MeetingStatus.COMPLETED)
        else None,
        meeting_url="https://zoom.us/j/123456789"
        if status in (MeetingStatus.SCHEDULED, MeetingStatus.COMPLETED)
        else None,
    )
    async_session.add(meeting)
    await async_session.commit()
    await async_session.refresh(meeting)

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await async_session.execute(
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


class TestCreateReview:
    async def test_mentee_can_review_completed_meeting(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        review = await create_review(
            async_session, meeting, mentee_user, rating=5, comment="Great session!"
        )

        assert review.rating == 5
        assert review.comment == "Great session!"
        assert review.reviewer_id == mentee_user.id
        assert review.meeting_id == meeting.id
        assert review.editable_until > datetime.now(UTC)

    async def test_cannot_review_requested_meeting(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.REQUESTED
        )

        with pytest.raises(MeetingNotCompletedError) as exc_info:
            await create_review(async_session, meeting, mentee_user, rating=5)

        assert "requested" in str(exc_info.value).lower()

    async def test_cannot_review_scheduled_meeting(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.SCHEDULED
        )

        with pytest.raises(MeetingNotCompletedError) as exc_info:
            await create_review(async_session, meeting, mentee_user, rating=5)

        assert "scheduled" in str(exc_info.value).lower()

    async def test_only_mentee_can_review(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        with pytest.raises(OnlyMenteeCanReviewError):
            await create_review(async_session, meeting, mentor_user, rating=5)

    async def test_cannot_review_twice(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        await create_review(async_session, meeting, mentee_user, rating=5)

        with pytest.raises(ReviewAlreadyExistsError):
            await create_review(async_session, meeting, mentee_user, rating=4)


class TestUpdateReview:
    async def test_can_update_within_window(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        review = await create_review(
            async_session, meeting, mentee_user, rating=4, comment="Good"
        )

        updated = await update_review(
            async_session, review, mentee_user, rating=5, comment="Actually great!"
        )

        assert updated.rating == 5
        assert updated.comment == "Actually great!"

    async def test_edit_rejected_after_window(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        review = await create_review(
            async_session, meeting, mentee_user, rating=4, comment="Good"
        )

        review.editable_until = datetime.now(UTC) - timedelta(days=1)
        await async_session.commit()

        with pytest.raises(ReviewEditWindowExpiredError):
            await update_review(async_session, review, mentee_user, rating=5)

    async def test_only_reviewer_can_edit(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)
        meeting = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        review = await create_review(async_session, meeting, mentee_user, rating=4)

        with pytest.raises(OnlyMenteeCanReviewError):
            await update_review(async_session, review, mentor_user, rating=5)


class TestListMentorReviews:
    async def test_lists_reviews_for_mentor(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)

        meeting1 = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )
        meeting2 = await create_meeting_with_status(
            async_session, mentorship, MeetingStatus.COMPLETED
        )

        await create_review(
            async_session, meeting1, mentee_user, rating=5, comment="Excellent"
        )
        await create_review(
            async_session, meeting2, mentee_user, rating=4, comment="Good"
        )

        reviews, total = await list_mentor_reviews(async_session, mentor_user.id)

        assert total == 2
        assert len(reviews) == 2

    async def test_pagination(self, async_session: AsyncSession) -> None:
        mentor_user, mentee_user, mentorship = await create_test_setup(async_session)

        for i in range(5):
            meeting = await create_meeting_with_status(
                async_session, mentorship, MeetingStatus.COMPLETED
            )
            await create_review(
                async_session, meeting, mentee_user, rating=5, comment=f"Review {i}"
            )

        reviews_page1, total = await list_mentor_reviews(
            async_session, mentor_user.id, page=1, page_size=2
        )
        reviews_page2, _ = await list_mentor_reviews(
            async_session, mentor_user.id, page=2, page_size=2
        )

        assert total == 5
        assert len(reviews_page1) == 2
        assert len(reviews_page2) == 2

        page1_ids = {r.id for r in reviews_page1}
        page2_ids = {r.id for r in reviews_page2}
        assert page1_ids.isdisjoint(page2_ids)
