"""Tests for mentorship lifecycle endpoints."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentorship import MentorshipStatus
from app.db.models.user import User
from app.services.mentorship_service import (
    DuplicateMentorshipError,
    InvalidStatusTransitionError,
    MentorNotFoundError,
    NotPartyToMentorshipError,
    SelfMentorshipError,
    accept_mentorship,
    create_mentorship,
    decline_mentorship,
    end_mentorship,
    get_mentorship_by_id,
    list_user_mentorships,
)


class TestCreateMentorship:
    """Tests for mentorship creation."""

    async def test_creates_mentorship_in_requested_status(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)

        assert mentorship.status == MentorshipStatus.REQUESTED
        assert mentorship.mentor_id == mentor_user.id
        assert mentorship.mentee_id == mentee_user.id

    async def test_creates_message_thread(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="mentor2@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="mentee2@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        await async_session.refresh(mentorship)

        full = await get_mentorship_by_id(async_session, mentorship.id)
        assert full is not None

        from sqlalchemy import select

        from app.db.models.message import Message
        from app.db.models.message_thread import MessageThread

        thread_result = await async_session.execute(
            select(MessageThread).where(MessageThread.mentorship_id == mentorship.id)
        )
        thread = thread_result.scalar_one()
        assert thread is not None

        msg_result = await async_session.execute(
            select(Message).where(Message.thread_id == thread.id)
        )
        messages = list(msg_result.scalars().all())
        assert len(messages) == 1
        assert messages[0].is_system is True

    async def test_rejects_self_mentorship(self, async_session: AsyncSession) -> None:
        user = User(cognito_sub=f"sub-{uuid4()}", email="self@test.com")
        async_session.add(user)
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        with pytest.raises(SelfMentorshipError):
            await create_mentorship(async_session, user, user.id)

    async def test_rejects_nonexistent_mentor(
        self, async_session: AsyncSession
    ) -> None:
        mentee = User(cognito_sub=f"sub-{uuid4()}", email="mentee3@test.com")
        async_session.add(mentee)
        await async_session.commit()

        with pytest.raises(MentorNotFoundError):
            await create_mentorship(async_session, mentee, uuid4())

    async def test_rejects_disabled_mentor(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="disabled@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="mentee4@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=False)
        async_session.add(mentor_profile)
        await async_session.commit()

        with pytest.raises(MentorNotFoundError):
            await create_mentorship(async_session, mentee_user, mentor_user.id)

    async def test_rejects_duplicate_mentorship(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="dup_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="dup_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        await create_mentorship(async_session, mentee_user, mentor_user.id)

        with pytest.raises(DuplicateMentorshipError):
            await create_mentorship(async_session, mentee_user, mentor_user.id)


class TestAcceptMentorship:
    """Tests for accepting mentorship requests."""

    async def test_transitions_to_active(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="accept_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="accept_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        assert mentorship.status == MentorshipStatus.REQUESTED

        mentorship = await accept_mentorship(async_session, mentorship, mentor_user)
        assert mentorship.status == MentorshipStatus.ACTIVE

    async def test_only_mentor_can_accept(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="only_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="only_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)

        with pytest.raises(NotPartyToMentorshipError):
            await accept_mentorship(async_session, mentorship, mentee_user)

    async def test_cannot_accept_non_requested(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user = User(
            cognito_sub=f"sub-{uuid4()}", email="non_req_mentor@test.com"
        )
        mentee_user = User(
            cognito_sub=f"sub-{uuid4()}", email="non_req_mentee@test.com"
        )
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        await accept_mentorship(async_session, mentorship, mentor_user)

        with pytest.raises(InvalidStatusTransitionError):
            await accept_mentorship(async_session, mentorship, mentor_user)


class TestDeclineMentorship:
    """Tests for declining mentorship requests."""

    async def test_transitions_to_declined(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="dec_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="dec_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)

        mentorship = await decline_mentorship(async_session, mentorship, mentor_user)
        assert mentorship.status == MentorshipStatus.DECLINED

    async def test_only_mentor_can_decline(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="dec2_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="dec2_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)

        with pytest.raises(NotPartyToMentorshipError):
            await decline_mentorship(async_session, mentorship, mentee_user)


class TestEndMentorship:
    """Tests for ending active mentorships."""

    async def test_mentor_can_end(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="end_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="end_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        await accept_mentorship(async_session, mentorship, mentor_user)

        mentorship = await end_mentorship(async_session, mentorship, mentor_user)
        assert mentorship.status == MentorshipStatus.ENDED

    async def test_mentee_can_end(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="end2_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="end2_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        await accept_mentorship(async_session, mentorship, mentor_user)

        mentorship = await end_mentorship(async_session, mentorship, mentee_user)
        assert mentorship.status == MentorshipStatus.ENDED

    async def test_cannot_end_requested(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="end3_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="end3_mentee@test.com")
        async_session.add_all([mentor_user, mentee_user])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)

        with pytest.raises(InvalidStatusTransitionError):
            await end_mentorship(async_session, mentorship, mentor_user)

    async def test_third_party_cannot_end(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="end4_mentor@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="end4_mentee@test.com")
        third_party = User(cognito_sub=f"sub-{uuid4()}", email="third@test.com")
        async_session.add_all([mentor_user, mentee_user, third_party])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        mentorship = await create_mentorship(async_session, mentee_user, mentor_user.id)
        await accept_mentorship(async_session, mentorship, mentor_user)

        with pytest.raises(NotPartyToMentorshipError):
            await end_mentorship(async_session, mentorship, third_party)


class TestListUserMentorships:
    """Tests for listing user's mentorships."""

    async def test_returns_mentorships_as_mentor(
        self, async_session: AsyncSession
    ) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="list_mentor@test.com")
        mentee1 = User(cognito_sub=f"sub-{uuid4()}", email="list_mentee1@test.com")
        mentee2 = User(cognito_sub=f"sub-{uuid4()}", email="list_mentee2@test.com")
        async_session.add_all([mentor_user, mentee1, mentee2])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        await create_mentorship(async_session, mentee1, mentor_user.id)
        await create_mentorship(async_session, mentee2, mentor_user.id)

        mentorships = await list_user_mentorships(async_session, mentor_user)
        assert len(mentorships) == 2

    async def test_returns_mentorships_as_mentee(
        self, async_session: AsyncSession
    ) -> None:
        mentor1 = User(cognito_sub=f"sub-{uuid4()}", email="list2_mentor1@test.com")
        mentor2 = User(cognito_sub=f"sub-{uuid4()}", email="list2_mentor2@test.com")
        mentee_user = User(cognito_sub=f"sub-{uuid4()}", email="list2_mentee@test.com")
        async_session.add_all([mentor1, mentor2, mentee_user])
        await async_session.commit()

        mp1 = MentorProfile(user_id=mentor1.id, is_enabled=True)
        mp2 = MentorProfile(user_id=mentor2.id, is_enabled=True)
        async_session.add_all([mp1, mp2])
        await async_session.commit()

        await create_mentorship(async_session, mentee_user, mentor1.id)
        await create_mentorship(async_session, mentee_user, mentor2.id)

        mentorships = await list_user_mentorships(async_session, mentee_user)
        assert len(mentorships) == 2

    async def test_filters_by_status(self, async_session: AsyncSession) -> None:
        mentor_user = User(cognito_sub=f"sub-{uuid4()}", email="filter_mentor@test.com")
        mentee1 = User(cognito_sub=f"sub-{uuid4()}", email="filter_mentee1@test.com")
        mentee2 = User(cognito_sub=f"sub-{uuid4()}", email="filter_mentee2@test.com")
        async_session.add_all([mentor_user, mentee1, mentee2])
        await async_session.commit()

        mentor_profile = MentorProfile(user_id=mentor_user.id, is_enabled=True)
        async_session.add(mentor_profile)
        await async_session.commit()

        m1 = await create_mentorship(async_session, mentee1, mentor_user.id)
        await create_mentorship(async_session, mentee2, mentor_user.id)
        await accept_mentorship(async_session, m1, mentor_user)

        active_only = await list_user_mentorships(
            async_session, mentor_user, status_filter=MentorshipStatus.ACTIVE
        )
        assert len(active_only) == 1
        assert active_only[0].status == MentorshipStatus.ACTIVE

        requested_only = await list_user_mentorships(
            async_session, mentor_user, status_filter=MentorshipStatus.REQUESTED
        )
        assert len(requested_only) == 1
        assert requested_only[0].status == MentorshipStatus.REQUESTED
