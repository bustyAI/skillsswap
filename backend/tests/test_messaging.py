"""Tests for messaging endpoints and service.

Tests cover:
- Sending messages as mentor in ACTIVE mentorship
- Sending messages as mentee in ACTIVE mentorship
- Rejecting messages in REQUESTED mentorship (403)
- Rejecting messages in ENDED mentorship (403)
- Rejecting messages from non-parties (403)
- Listing messages with cursor-based pagination
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mentor_profile import MentorProfile
from app.db.models.user import User
from app.services.mentorship_service import (
    accept_mentorship,
    create_mentorship,
    end_mentorship,
)
from app.services.message_service import (
    MentorshipNotActiveError,
    NotPartyToMentorshipError,
    list_messages,
    send_message,
)


class TestSendMessage:
    """Tests for sending messages in mentorships."""

    async def test_mentor_can_send_message_in_active_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Mentor can send a message in an ACTIVE mentorship."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="msg_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="msg_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        message = await send_message(
            async_session, mentorship, mentor_user, "Hello from mentor!"
        )

        assert message.content == "Hello from mentor!"
        assert message.sender_id == mentor_user.id
        assert message.is_system is False

    async def test_mentee_can_send_message_in_active_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Mentee can send a message in an ACTIVE mentorship."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="msg2_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="msg2_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        message = await send_message(
            async_session, mentorship, mentee_user, "Hello from mentee!"
        )

        assert message.content == "Hello from mentee!"
        assert message.sender_id == mentee_user.id
        assert message.is_system is False

    async def test_cannot_send_message_in_requested_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Cannot send message in REQUESTED mentorship (not yet accepted)."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="msg3_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="msg3_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        # Note: mentorship is in REQUESTED status, not accepted

        with pytest.raises(MentorshipNotActiveError) as exc_info:
            await send_message(
                async_session, mentorship, mentee_user, "Should not work"
            )

        assert "requested" in str(exc_info.value).lower()

    async def test_cannot_send_message_in_ended_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Cannot send message in ENDED mentorship."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="msg4_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="msg4_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)
        mentorship = await end_mentorship(async_session, mentorship, mentor_user)

        with pytest.raises(MentorshipNotActiveError) as exc_info:
            await send_message(
                async_session, mentorship, mentee_user, "Should not work"
            )

        assert "ended" in str(exc_info.value).lower()

    async def test_cannot_send_message_in_someone_elses_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Third party cannot send message in mentorship they're not part of."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="msg5_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="msg5_mentee@test.com")
        third_party = User(cognito_sub=f"sub-{uuid4()}", email="msg5_third@test.com")
        async_session.add_all([mentor_user, mentee_user, third_party])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        with pytest.raises(NotPartyToMentorshipError):
            await send_message(
                async_session, mentorship, third_party, "Should not work"
            )


class TestListMessages:
    """Tests for listing messages with pagination."""

    async def test_mentor_can_list_messages(self, async_session: AsyncSession) -> None:
        """Mentor can list messages in their mentorship."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="list_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="list_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        # Send a message
        await send_message(async_session, mentorship, mentor_user, "Test message")

        messages, next_cursor, has_more = await list_messages(
            async_session, mentorship, mentor_user
        )

        # Should have system message + our message
        assert len(messages) >= 1
        assert any(m.content == "Test message" for m in messages)
        assert has_more is False

    async def test_mentee_can_list_messages(self, async_session: AsyncSession) -> None:
        """Mentee can list messages in their mentorship."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="list2_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="list2_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        # Send a message
        await send_message(async_session, mentorship, mentee_user, "Mentee message")

        messages, next_cursor, has_more = await list_messages(
            async_session, mentorship, mentee_user
        )

        assert len(messages) >= 1
        assert any(m.content == "Mentee message" for m in messages)

    async def test_cannot_list_messages_in_someone_elses_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        """Third party cannot list messages in mentorship they're not part of."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="list3_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="list3_mentee@test.com")
        third_party = User(cognito_sub=f"sub-{uuid4()}", email="list3_third@test.com")
        async_session.add_all([mentor_user, mentee_user, third_party])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        with pytest.raises(NotPartyToMentorshipError):
            await list_messages(async_session, mentorship, third_party)

    async def test_messages_returned_newest_first(
        self, async_session: AsyncSession
    ) -> None:
        """Messages are returned in newest-first order."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="order_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="order_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        # Send messages in order
        await send_message(async_session, mentorship, mentor_user, "First message")
        await send_message(async_session, mentorship, mentee_user, "Second message")
        await send_message(async_session, mentorship, mentor_user, "Third message")

        messages, _, _ = await list_messages(async_session, mentorship, mentor_user)

        # Filter out system message and check order
        user_messages = [m for m in messages if not m.is_system]
        assert len(user_messages) == 3
        assert user_messages[0].content == "Third message"
        assert user_messages[1].content == "Second message"
        assert user_messages[2].content == "First message"

    async def test_pagination_with_limit(self, async_session: AsyncSession) -> None:
        """Pagination respects limit parameter."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="page_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="page_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        # Send 5 messages
        for i in range(5):
            await send_message(async_session, mentorship, mentor_user, f"Message {i}")

        # Fetch with limit of 2
        messages, next_cursor, has_more = await list_messages(
            async_session, mentorship, mentor_user, limit=2
        )

        assert len(messages) == 2
        assert has_more is True
        assert next_cursor is not None

    async def test_pagination_cursor_fetches_older_messages(
        self, async_session: AsyncSession
    ) -> None:
        """Using cursor fetches older messages."""
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="cursor_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="cursor_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)

        # Send 5 messages
        for i in range(5):
            await send_message(async_session, mentorship, mentor_user, f"Message {i}")

        # Fetch first page
        messages_page1, next_cursor, has_more = await list_messages(
            async_session, mentorship, mentor_user, limit=2
        )

        assert len(messages_page1) == 2
        assert has_more is True
        assert next_cursor is not None

        # Fetch second page using cursor
        messages_page2, next_cursor2, has_more2 = await list_messages(
            async_session, mentorship, mentor_user, limit=2, cursor=next_cursor
        )

        assert len(messages_page2) == 2
        # Messages should be different (older)
        page1_ids = {m.id for m in messages_page1}
        page2_ids = {m.id for m in messages_page2}
        assert page1_ids.isdisjoint(page2_ids)
