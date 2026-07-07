from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.validators import MeetingURLValidationError, validate_meeting_url
from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.user import User


class MeetingError(Exception):
    pass


class MeetorshipNotFoundError(MeetingError):
    pass


class MentorshipNotActiveError(MeetingError):
    pass


class NotPartyToMeetingError(MeetingError):
    pass


class MeetingNotFoundError(MeetingError):
    pass


class InvalidMeetingTransitionError(MeetingError):
    pass


class OnlyMentorCanScheduleError(MeetingError):
    pass


class OnlyMenteeCanRequestError(MeetingError):
    pass


class MeetingNotYetScheduledTimeError(MeetingError):
    pass


class InvalidMeetingURLError(MeetingError):
    pass


async def get_meeting_by_id(
    db: AsyncSession,
    meeting_id: UUID,
    *,
    include_mentorship: bool = False,
) -> Meeting | None:
    query = select(Meeting).where(Meeting.id == meeting_id)
    if include_mentorship:
        query = query.options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_meeting(
    db: AsyncSession,
    mentorship: Mentorship,
    user: User,
) -> Meeting:
    if user.id != mentorship.mentee_id:
        raise OnlyMenteeCanRequestError("Only the mentee can request a meeting")

    if mentorship.status != MentorshipStatus.ACTIVE:
        raise MentorshipNotActiveError(
            f"Cannot create meeting for mentorship in {mentorship.status.value} status"
        )

    meeting = Meeting(
        mentorship_id=mentorship.id,
        status=MeetingStatus.REQUESTED,
        scheduled_time=None,
        meeting_url=None,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def schedule_meeting(
    db: AsyncSession,
    meeting: Meeting,
    user: User,
    scheduled_time: datetime,
    meeting_url: str,
) -> Meeting:
    mentorship = meeting.mentorship

    if user.id != mentorship.mentor_id:
        raise OnlyMentorCanScheduleError("Only the mentor can schedule a meeting")

    if meeting.status != MeetingStatus.REQUESTED:
        raise InvalidMeetingTransitionError(
            f"Cannot schedule meeting in {meeting.status.value} status"
        )

    try:
        validated_url = validate_meeting_url(meeting_url)
    except MeetingURLValidationError as e:
        raise InvalidMeetingURLError(str(e)) from e

    meeting.scheduled_time = scheduled_time
    meeting.meeting_url = validated_url
    meeting.status = MeetingStatus.SCHEDULED

    await db.commit()
    await db.refresh(meeting)

    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def cancel_meeting(
    db: AsyncSession,
    meeting: Meeting,
    user: User,
) -> Meeting:
    mentorship = meeting.mentorship

    if user.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise NotPartyToMeetingError("You are not a party to this meeting")

    if meeting.status not in (MeetingStatus.REQUESTED, MeetingStatus.SCHEDULED):
        raise InvalidMeetingTransitionError(
            f"Cannot cancel meeting in {meeting.status.value} status"
        )

    meeting.status = MeetingStatus.CANCELLED

    await db.commit()
    await db.refresh(meeting)

    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def complete_meeting(
    db: AsyncSession,
    meeting: Meeting,
    user: User,
) -> Meeting:
    mentorship = meeting.mentorship

    if user.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise NotPartyToMeetingError("You are not a party to this meeting")

    if meeting.status != MeetingStatus.SCHEDULED:
        raise InvalidMeetingTransitionError(
            f"Cannot complete meeting in {meeting.status.value} status"
        )

    now = datetime.now(UTC)
    if meeting.scheduled_time and meeting.scheduled_time > now:
        raise MeetingNotYetScheduledTimeError(
            "Cannot complete meeting before its scheduled time"
        )

    meeting.status = MeetingStatus.COMPLETED

    await db.commit()
    await db.refresh(meeting)

    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def list_user_meetings(
    db: AsyncSession,
    user: User,
    *,
    upcoming_only: bool = False,
) -> list[Meeting]:
    query = (
        select(Meeting)
        .join(Mentorship)
        .where(
            or_(
                Mentorship.mentor_id == user.id,
                Mentorship.mentee_id == user.id,
            )
        )
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
        .order_by(Meeting.scheduled_time.asc().nulls_last(), Meeting.created_at.desc())
    )

    if upcoming_only:
        now = datetime.now(UTC)
        query = query.where(
            Meeting.status == MeetingStatus.SCHEDULED,
            Meeting.scheduled_time > now,
        )

    result = await db.execute(query)
    return list(result.scalars().all())


async def list_mentorship_meetings(
    db: AsyncSession,
    mentorship_id: UUID,
) -> list[Meeting]:
    """List all meetings for a specific mentorship."""
    query = (
        select(Meeting)
        .where(Meeting.mentorship_id == mentorship_id)
        .options(
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentor),
            selectinload(Meeting.mentorship).selectinload(Mentorship.mentee),
        )
        .order_by(Meeting.scheduled_time.asc().nulls_last(), Meeting.created_at.desc())
    )

    result = await db.execute(query)
    return list(result.scalars().all())
