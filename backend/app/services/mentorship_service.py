"""Mentorship service - business logic for mentorship operations."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.message import Message
from app.db.models.message_thread import MessageThread
from app.db.models.user import User


class MentorshipError(Exception):
    """Base exception for mentorship operations."""

    pass


class MentorNotFoundError(MentorshipError):
    """Raised when the target mentor doesn't exist or is not enabled."""

    pass


class SelfMentorshipError(MentorshipError):
    """Raised when a user tries to mentor themselves."""

    pass


class DuplicateMentorshipError(MentorshipError):
    """Raised when a mentorship already exists between the two users."""

    pass


class MentorshipNotFoundError(MentorshipError):
    """Raised when mentorship is not found."""

    pass


class InvalidStatusTransitionError(MentorshipError):
    """Raised when a status transition is not allowed."""

    pass


class NotPartyToMentorshipError(MentorshipError):
    """Raised when user is not a party to the mentorship."""

    pass


async def get_mentorship_by_id(
    db: AsyncSession,
    mentorship_id: UUID,
    *,
    include_users: bool = False,
) -> Mentorship | None:
    """Get a mentorship by ID, optionally loading related users."""
    query = select(Mentorship).where(Mentorship.id == mentorship_id)
    if include_users:
        query = query.options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_mentorship(
    db: AsyncSession,
    mentee: User,
    mentor_id: UUID,
) -> Mentorship:
    """Create a new mentorship request.

    Creates the mentorship in REQUESTED status, along with a MessageThread
    and a system message announcing the request.

    Raises:
        SelfMentorshipError: If mentee tries to mentor themselves.
        MentorNotFoundError: If mentor doesn't exist or is disabled.
        DuplicateMentorshipError: If relationship already exists.
    """
    if mentee.id == mentor_id:
        raise SelfMentorshipError("Cannot request mentorship from yourself")

    mentor_profile = await db.execute(
        select(MentorProfile)
        .join(User)
        .where(
            MentorProfile.user_id == mentor_id,
            MentorProfile.is_enabled.is_(True),
            User.deleted_at.is_(None),
        )
    )
    if mentor_profile.scalar_one_or_none() is None:
        raise MentorNotFoundError("Mentor not found or not accepting requests")

    # Check for any existing mentorship between these users
    existing_result = await db.execute(
        select(Mentorship).where(
            Mentorship.mentor_id == mentor_id,
            Mentorship.mentee_id == mentee.id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        # Block if already active or pending
        if existing.status in (MentorshipStatus.REQUESTED, MentorshipStatus.ACTIVE):
            raise DuplicateMentorshipError("Mentorship already exists with this mentor")

        # Reactivate ended/declined mentorship
        existing.status = MentorshipStatus.REQUESTED
        mentorship = existing
        await db.flush()

        # Get existing thread and add system message
        thread_result = await db.execute(
            select(MessageThread).where(MessageThread.mentorship_id == mentorship.id)
        )
        thread = thread_result.scalar_one_or_none()
        if thread:
            system_message = Message(
                thread_id=thread.id,
                sender_id=None,
                content="Mentorship request renewed.",
                is_system=True,
            )
            db.add(system_message)
    else:
        # Create new mentorship
        mentorship = Mentorship(
            mentor_id=mentor_id,
            mentee_id=mentee.id,
            status=MentorshipStatus.REQUESTED,
        )
        db.add(mentorship)
        await db.flush()

        thread = MessageThread(mentorship_id=mentorship.id)
        db.add(thread)
        await db.flush()

        system_message = Message(
            thread_id=thread.id,
            sender_id=None,
            content="Mentorship request created.",
            is_system=True,
        )
        db.add(system_message)

    await db.commit()
    await db.refresh(mentorship)

    result = await db.execute(
        select(Mentorship)
        .where(Mentorship.id == mentorship.id)
        .options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def accept_mentorship(
    db: AsyncSession,
    mentorship: Mentorship,
    user: User,
) -> Mentorship:
    """Accept a mentorship request (mentor only).

    Raises:
        NotPartyToMentorshipError: If user is not the mentor.
        InvalidStatusTransitionError: If status is not REQUESTED.
    """
    if mentorship.mentor_id != user.id:
        raise NotPartyToMentorshipError("Only the mentor can accept the request")

    if mentorship.status != MentorshipStatus.REQUESTED:
        raise InvalidStatusTransitionError(
            f"Cannot accept mentorship in {mentorship.status.value} status"
        )

    mentorship.status = MentorshipStatus.ACTIVE
    await db.commit()
    await db.refresh(mentorship)

    result = await db.execute(
        select(Mentorship)
        .where(Mentorship.id == mentorship.id)
        .options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def decline_mentorship(
    db: AsyncSession,
    mentorship: Mentorship,
    user: User,
) -> Mentorship:
    """Decline a mentorship request (mentor only).

    Raises:
        NotPartyToMentorshipError: If user is not the mentor.
        InvalidStatusTransitionError: If status is not REQUESTED.
    """
    if mentorship.mentor_id != user.id:
        raise NotPartyToMentorshipError("Only the mentor can decline the request")

    if mentorship.status != MentorshipStatus.REQUESTED:
        raise InvalidStatusTransitionError(
            f"Cannot decline mentorship in {mentorship.status.value} status"
        )

    mentorship.status = MentorshipStatus.DECLINED
    await db.commit()
    await db.refresh(mentorship)

    result = await db.execute(
        select(Mentorship)
        .where(Mentorship.id == mentorship.id)
        .options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def end_mentorship(
    db: AsyncSession,
    mentorship: Mentorship,
    user: User,
) -> Mentorship:
    """End an active mentorship (either party).

    Raises:
        NotPartyToMentorshipError: If user is not a party.
        InvalidStatusTransitionError: If status is not ACTIVE.
    """
    if user.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise NotPartyToMentorshipError("You are not a party to this mentorship")

    if mentorship.status != MentorshipStatus.ACTIVE:
        raise InvalidStatusTransitionError(
            f"Cannot end mentorship in {mentorship.status.value} status"
        )

    mentorship.status = MentorshipStatus.ENDED
    await db.commit()
    await db.refresh(mentorship)

    result = await db.execute(
        select(Mentorship)
        .where(Mentorship.id == mentorship.id)
        .options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
    )
    return result.scalar_one()


async def list_user_mentorships(
    db: AsyncSession,
    user: User,
    *,
    status_filter: MentorshipStatus | None = None,
) -> list[Mentorship]:
    """List all mentorships where user is mentor or mentee."""
    query = (
        select(Mentorship)
        .where(
            or_(
                Mentorship.mentor_id == user.id,
                Mentorship.mentee_id == user.id,
            )
        )
        .options(
            selectinload(Mentorship.mentor),
            selectinload(Mentorship.mentee),
        )
        .order_by(Mentorship.updated_at.desc())
    )

    if status_filter is not None:
        query = query.where(Mentorship.status == status_filter)

    result = await db.execute(query)
    return list(result.scalars().all())
