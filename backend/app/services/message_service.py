"""Message service - business logic for messaging operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.mentorship import Mentorship, MentorshipStatus
from app.db.models.message import Message
from app.db.models.message_thread import MessageThread
from app.db.models.user import User


class MessageError(Exception):
    """Base exception for message operations."""

    pass


class MentorshipNotActiveError(MessageError):
    """Raised when trying to send a message in a non-active mentorship."""

    pass


class NotPartyToMentorshipError(MessageError):
    """Raised when user is not a party to the mentorship."""

    pass


class ThreadNotFoundError(MessageError):
    """Raised when message thread is not found."""

    pass


async def get_thread_for_mentorship(
    db: AsyncSession,
    mentorship: Mentorship,
) -> MessageThread | None:
    """Get the message thread for a mentorship."""
    result = await db.execute(
        select(MessageThread).where(MessageThread.mentorship_id == mentorship.id)
    )
    return result.scalar_one_or_none()


async def send_message(
    db: AsyncSession,
    mentorship: Mentorship,
    sender: User,
    content: str,
) -> Message:
    """Send a message in a mentorship thread.

    Raises:
        MentorshipNotActiveError: If mentorship is not ACTIVE.
        NotPartyToMentorshipError: If sender is not a party to the mentorship.
        ThreadNotFoundError: If no message thread exists.
    """
    if mentorship.status != MentorshipStatus.ACTIVE:
        raise MentorshipNotActiveError(
            f"Cannot send messages in {mentorship.status.value} mentorship"
        )

    if sender.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise NotPartyToMentorshipError("You are not a party to this mentorship")

    thread = await get_thread_for_mentorship(db, mentorship)
    if thread is None:
        raise ThreadNotFoundError("Message thread not found")

    message = Message(
        thread_id=thread.id,
        sender_id=sender.id,
        content=content,
        is_system=False,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    result = await db.execute(
        select(Message)
        .where(Message.id == message.id)
        .options(selectinload(Message.sender))
    )
    return result.scalar_one()


async def list_messages(
    db: AsyncSession,
    mentorship: Mentorship,
    user: User,
    *,
    limit: int = 50,
    cursor: datetime | None = None,
) -> tuple[list[Message], datetime | None, bool]:
    """List messages in a mentorship thread with cursor-based pagination.

    Returns newest first. Cursor is the created_at of the last message.

    Returns:
        Tuple of (messages, next_cursor, has_more)

    Raises:
        NotPartyToMentorshipError: If user is not a party to the mentorship.
        ThreadNotFoundError: If no message thread exists.
    """
    if user.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise NotPartyToMentorshipError("You are not a party to this mentorship")

    thread = await get_thread_for_mentorship(db, mentorship)
    if thread is None:
        raise ThreadNotFoundError("Message thread not found")

    query = (
        select(Message)
        .where(Message.thread_id == thread.id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.desc())
        .limit(limit + 1)
    )

    if cursor is not None:
        query = query.where(Message.created_at < cursor)

    result = await db.execute(query)
    messages = list(result.scalars().all())

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    next_cursor = messages[-1].created_at if messages and has_more else None

    return messages, next_cursor, has_more
