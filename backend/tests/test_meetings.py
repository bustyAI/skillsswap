from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.user import User
from app.services.meeting_service import (
    InvalidMeetingTransitionError,
    InvalidMeetingURLError,
    MeetingNotYetScheduledTimeError,
    MentorshipNotActiveError,
    NotPartyToMeetingError,
    OnlyMenteeCanRequestError,
    OnlyMentorCanScheduleError,
    cancel_meeting,
    complete_meeting,
    create_meeting,
    get_meeting_by_id,
    list_user_meetings,
    schedule_meeting,
)
from app.services.mentorship_service import accept_mentorship, create_mentorship


async def _setup_active_mentorship(
    db: AsyncSession,
) -> tuple[User, User, Mentorship]:
    mentor_user = User(cognito_sub=f"sub-{uuid4()}", email=f"mentor-{uuid4()}@test.com")
    mentee_user = User(cognito_sub=f"sub-{uuid4()}", email=f"mentee-{uuid4()}@test.com")
    db.add_all([mentor_user, mentee_user])
    await db.commit()

    mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
    db.add(mentor_profile)
    await db.commit()

    mentorship = await create_mentorship(db, mentee_user, mentor_user.id)
    mentorship = await accept_mentorship(db, mentorship, mentor_user)

    return mentor_user, mentee_user, mentorship


class TestCreateMeeting:
    async def test_creates_meeting_in_requested_status(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        meeting = await create_meeting(async_session, mentorship, mentee)

        assert meeting.status == MeetingStatus.REQUESTED
        assert meeting.mentorship_id == mentorship.id
        assert meeting.scheduled_time is None
        assert meeting.meeting_url is None

    async def test_only_mentee_can_request(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        with pytest.raises(OnlyMenteeCanRequestError):
            await create_meeting(async_session, mentorship, mentor)

    async def test_requires_active_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user = User(
            cognito_sub=f"sub-{uuid4()}", email=f"mentor-{uuid4()}@test.com"
        )
        mentee_user = User(
            cognito_sub=f"sub-{uuid4()}", email=f"mentee-{uuid4()}@test.com"
        )
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        assert mentorship.status == MentorshipStatus.REQUESTED

        with pytest.raises(MentorshipNotActiveError):
            await create_meeting(async_session, mentorship, mentee_user)


class TestScheduleMeeting:
    async def test_schedules_meeting_with_time_and_url(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        meeting_url = "https://zoom.us/j/123456"

        meeting = await schedule_meeting(
            async_session, meeting, mentor, scheduled_time, meeting_url
        )

        assert meeting.status == MeetingStatus.SCHEDULED
        assert meeting.scheduled_time == scheduled_time
        assert meeting.meeting_url == meeting_url

    async def test_only_mentor_can_schedule(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        meeting_url = "https://zoom.us/j/123456"

        with pytest.raises(OnlyMentorCanScheduleError):
            await schedule_meeting(
                async_session, meeting, mentee, scheduled_time, meeting_url
            )

    async def test_rejects_invalid_url(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        invalid_url = "https://evil.com/meeting"

        with pytest.raises(InvalidMeetingURLError):
            await schedule_meeting(
                async_session, meeting, mentor, scheduled_time, invalid_url
            )

    async def test_rejects_http_url(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)

        with pytest.raises(InvalidMeetingURLError):
            await schedule_meeting(
                async_session, meeting, mentor, scheduled_time, "http://zoom.us/j/123"
            )

    async def test_cannot_schedule_already_scheduled(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        meeting_url = "https://zoom.us/j/123456"

        meeting = await schedule_meeting(
            async_session, meeting, mentor, scheduled_time, meeting_url
        )

        with pytest.raises(InvalidMeetingTransitionError):
            await schedule_meeting(
                async_session, meeting, mentor, scheduled_time, meeting_url
            )

    async def test_accepts_valid_meeting_domains(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        valid_urls = [
            "https://zoom.us/j/123",
            "https://us02web.zoom.us/j/123",
            "https://meet.google.com/abc-defg-hij",
            "https://teams.microsoft.com/l/meetup-join/abc",
            "https://whereby.com/my-room",
        ]

        for i, url in enumerate(valid_urls):
            meeting = await create_meeting(async_session, mentorship, mentee)
            scheduled_time = datetime.now(UTC) + timedelta(days=i + 1)
            meeting = await schedule_meeting(
                async_session, meeting, mentor, scheduled_time, url
            )
            assert meeting.status == MeetingStatus.SCHEDULED


class TestCancelMeeting:
    async def test_mentor_can_cancel(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        meeting = await cancel_meeting(async_session, meeting, mentor)
        assert meeting.status == MeetingStatus.CANCELLED

    async def test_mentee_can_cancel(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        meeting = await cancel_meeting(async_session, meeting, mentee)
        assert meeting.status == MeetingStatus.CANCELLED

    async def test_can_cancel_scheduled_meeting(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        meeting = await schedule_meeting(
            async_session, meeting, mentor, scheduled_time, "https://zoom.us/j/123"
        )

        meeting = await cancel_meeting(async_session, meeting, mentor)
        assert meeting.status == MeetingStatus.CANCELLED

    async def test_third_party_cannot_cancel(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        third_party = User(
            cognito_sub=f"sub-{uuid4()}", email=f"third-{uuid4()}@test.com"
        )
        async_session.add(third_party)
        await async_session.commit()

        with pytest.raises(NotPartyToMeetingError):
            await cancel_meeting(async_session, meeting, third_party)

    async def test_cannot_cancel_completed(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        past_time = datetime.now(UTC) - timedelta(hours=1)
        meeting.scheduled_time = past_time
        meeting.meeting_url = "https://zoom.us/j/123"
        meeting.status = MeetingStatus.SCHEDULED
        await async_session.commit()
        await async_session.refresh(meeting)

        meeting = await get_meeting_by_id(
            async_session, meeting.id, include_mentorship=True
        )
        meeting = await complete_meeting(async_session, meeting, mentor)

        with pytest.raises(InvalidMeetingTransitionError):
            await cancel_meeting(async_session, meeting, mentor)


class TestCompleteMeeting:
    async def test_completes_after_scheduled_time(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        past_time = datetime.now(UTC) - timedelta(hours=1)
        meeting.scheduled_time = past_time
        meeting.meeting_url = "https://zoom.us/j/123"
        meeting.status = MeetingStatus.SCHEDULED
        await async_session.commit()
        await async_session.refresh(meeting)

        meeting = await get_meeting_by_id(
            async_session, meeting.id, include_mentorship=True
        )
        meeting = await complete_meeting(async_session, meeting, mentor)
        assert meeting.status == MeetingStatus.COMPLETED

    async def test_cannot_complete_before_scheduled_time(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        future_time = datetime.now(UTC) + timedelta(hours=1)
        meeting = await schedule_meeting(
            async_session, meeting, mentor, future_time, "https://zoom.us/j/123"
        )

        with pytest.raises(MeetingNotYetScheduledTimeError):
            await complete_meeting(async_session, meeting, mentee)

    async def test_cannot_complete_requested_meeting(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)
        meeting = await create_meeting(async_session, mentorship, mentee)

        with pytest.raises(InvalidMeetingTransitionError):
            await complete_meeting(async_session, meeting, mentee)


class TestListUserMeetings:
    async def test_returns_user_meetings(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        await create_meeting(async_session, mentorship, mentee)
        await create_meeting(async_session, mentorship, mentee)

        mentor_meetings = await list_user_meetings(async_session, mentor)
        assert len(mentor_meetings) == 2

        mentee_meetings = await list_user_meetings(async_session, mentee)
        assert len(mentee_meetings) == 2

    async def test_upcoming_only_filter(self, async_session: AsyncSession) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        meeting1 = await create_meeting(async_session, mentorship, mentee)
        await create_meeting(
            async_session, mentorship, mentee
        )  # meeting2, not scheduled

        future_time = datetime.now(UTC) + timedelta(days=1)
        await schedule_meeting(
            async_session, meeting1, mentor, future_time, "https://zoom.us/j/1"
        )

        upcoming = await list_user_meetings(async_session, mentor, upcoming_only=True)
        assert len(upcoming) == 1
        assert upcoming[0].id == meeting1.id


class TestDBCheckConstraint:
    async def test_check_constraint_requires_url_and_time_for_scheduled(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.SCHEDULED,
            scheduled_time=None,
            meeting_url=None,
        )
        async_session.add(meeting)

        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await async_session.commit()

    async def test_check_constraint_allows_scheduled_with_url_and_time(
        self, async_session: AsyncSession
    ) -> None:
        mentor, mentee, mentorship = await _setup_active_mentorship(async_session)

        meeting = Meeting(
            mentorship_id=mentorship.id,
            status=MeetingStatus.SCHEDULED,
            scheduled_time=datetime.now(UTC) + timedelta(days=1),
            meeting_url="https://zoom.us/j/123",
        )
        async_session.add(meeting)
        await async_session.commit()

        result = await async_session.execute(
            select(Meeting).where(Meeting.id == meeting.id)
        )
        saved = result.scalar_one()
        assert saved.status == MeetingStatus.SCHEDULED
