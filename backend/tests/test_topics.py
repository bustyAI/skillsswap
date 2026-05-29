"""Tests for topic discovery endpoints."""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mentor_profile import MentorProfile
from app.db.models.mentor_topic import MentorTopic
from app.db.models.topic import Topic
from app.db.models.user import User


class TestListTopics:
    """Tests for GET /api/topics."""

    async def test_list_root_topics(self, async_session: AsyncSession) -> None:
        """Returns root-level topics when no parent_topic_id provided."""
        # Create root topics
        topic1 = Topic(name="Programming", description="Software development")
        topic2 = Topic(name="Design", description="Visual design")
        async_session.add_all([topic1, topic2])
        await async_session.commit()

        from app.services.topic_service import list_topics

        topics, total = await list_topics(async_session)

        assert total >= 2
        names = [t.name for t in topics]
        assert "Programming" in names
        assert "Design" in names

    async def test_list_child_topics(self, async_session: AsyncSession) -> None:
        """Returns child topics when parent_topic_id is provided."""
        parent = Topic(name="ParentTopic")
        async_session.add(parent)
        await async_session.commit()

        child1 = Topic(name="Child1", parent_topic_id=parent.id)
        child2 = Topic(name="Child2", parent_topic_id=parent.id)
        unrelated = Topic(name="Unrelated")
        async_session.add_all([child1, child2, unrelated])
        await async_session.commit()

        from app.services.topic_service import list_topics

        topics, total = await list_topics(async_session, parent_topic_id=parent.id)

        assert total == 2
        names = [t.name for t in topics]
        assert "Child1" in names
        assert "Child2" in names
        assert "Unrelated" not in names

    async def test_list_topics_pagination(self, async_session: AsyncSession) -> None:
        """Pagination works correctly."""
        for i in range(5):
            async_session.add(Topic(name=f"Topic{i:02d}"))
        await async_session.commit()

        from app.services.topic_service import list_topics

        page1, total = await list_topics(async_session, page=1, page_size=2)
        page2, _ = await list_topics(async_session, page=2, page_size=2)

        assert total >= 5
        assert len(page1) == 2
        assert len(page2) == 2
        page1_names = {t.name for t in page1}
        page2_names = {t.name for t in page2}
        assert page1_names.isdisjoint(page2_names)


class TestGetTopicById:
    """Tests for GET /api/topics/{topic_id}."""

    async def test_get_existing_topic(self, async_session: AsyncSession) -> None:
        """Returns topic when it exists."""
        topic = Topic(name="TestTopic", description="A test topic")
        async_session.add(topic)
        await async_session.commit()

        from app.services.topic_service import get_topic_by_id

        result = await get_topic_by_id(async_session, topic.id)

        assert result is not None
        assert result.name == "TestTopic"
        assert result.description == "A test topic"

    async def test_get_nonexistent_topic(self, async_session: AsyncSession) -> None:
        """Returns None for nonexistent topic."""
        from app.services.topic_service import get_topic_by_id

        result = await get_topic_by_id(async_session, uuid4())

        assert result is None


class TestGetMentorsForTopic:
    """Tests for GET /api/topics/{topic_id}/mentors."""

    async def test_returns_mentors_for_topic(self, async_session: AsyncSession) -> None:
        """Returns mentors who have the specified topic."""
        topic = Topic(name="Python")
        other_topic = Topic(name="JavaScript")
        async_session.add_all([topic, other_topic])
        await async_session.commit()

        user1 = User(cognito_sub=f"sub-{uuid4()}", email="mentor1@test.com")
        user2 = User(cognito_sub=f"sub-{uuid4()}", email="mentor2@test.com")
        async_session.add_all([user1, user2])
        await async_session.commit()

        mentor1 = MentorProfile(user_id=user1.id, headline="Python Expert")
        mentor2 = MentorProfile(user_id=user2.id, headline="JS Expert")
        async_session.add_all([mentor1, mentor2])
        await async_session.commit()

        mt1 = MentorTopic(mentor_profile_id=mentor1.id, topic_id=topic.id)
        mt2 = MentorTopic(mentor_profile_id=mentor2.id, topic_id=other_topic.id)
        async_session.add_all([mt1, mt2])
        await async_session.commit()

        from app.services.topic_service import get_mentors_for_topic

        mentors, total = await get_mentors_for_topic(async_session, topic.id)

        assert total == 1
        assert mentors[0].headline == "Python Expert"

    async def test_mentors_ordered_by_rating(self, async_session: AsyncSession) -> None:
        """Mentors are ordered by rating_avg descending."""
        topic = Topic(name="TestOrdering")
        async_session.add(topic)
        await async_session.commit()

        users = []
        mentors = []
        ratings = [Decimal("4.5"), Decimal("3.0"), Decimal("5.0"), None]

        for i, rating in enumerate(ratings):
            user = User(cognito_sub=f"sub-order-{uuid4()}", email=f"order{i}@test.com")
            async_session.add(user)
            await async_session.commit()
            users.append(user)

            mentor = MentorProfile(
                user_id=user.id,
                headline=f"Mentor{i}",
                rating_avg=rating,
                rating_count=10 if rating else 0,
            )
            async_session.add(mentor)
            await async_session.commit()
            mentors.append(mentor)

            mt = MentorTopic(mentor_profile_id=mentor.id, topic_id=topic.id)
            async_session.add(mt)

        await async_session.commit()

        from app.services.topic_service import get_mentors_for_topic

        result, _ = await get_mentors_for_topic(async_session, topic.id)

        result_ratings = [m.rating_avg for m in result]
        assert result_ratings[0] == Decimal("5.0")
        assert result_ratings[1] == Decimal("4.5")
        assert result_ratings[2] == Decimal("3.0")
        assert result_ratings[3] is None

    async def test_excludes_disabled_mentors(self, async_session: AsyncSession) -> None:
        """Disabled mentors are not returned."""
        topic = Topic(name="FilterTest")
        async_session.add(topic)
        await async_session.commit()

        user1 = User(cognito_sub=f"sub-{uuid4()}", email="enabled@test.com")
        user2 = User(cognito_sub=f"sub-{uuid4()}", email="disabled@test.com")
        async_session.add_all([user1, user2])
        await async_session.commit()

        enabled_mentor = MentorProfile(user_id=user1.id, is_enabled=True)
        disabled_mentor = MentorProfile(user_id=user2.id, is_enabled=False)
        async_session.add_all([enabled_mentor, disabled_mentor])
        await async_session.commit()

        async_session.add(
            MentorTopic(mentor_profile_id=enabled_mentor.id, topic_id=topic.id)
        )
        async_session.add(
            MentorTopic(mentor_profile_id=disabled_mentor.id, topic_id=topic.id)
        )
        await async_session.commit()

        from app.services.topic_service import get_mentors_for_topic

        mentors, total = await get_mentors_for_topic(async_session, topic.id)

        assert total == 1
        assert mentors[0].is_enabled is True

    async def test_excludes_deleted_users(self, async_session: AsyncSession) -> None:
        """Mentors of deleted users are not returned."""
        from datetime import UTC, datetime

        topic = Topic(name="DeletedUserTest")
        async_session.add(topic)
        await async_session.commit()

        active_user = User(cognito_sub=f"sub-{uuid4()}", email="active@test.com")
        deleted_user = User(
            cognito_sub=f"sub-{uuid4()}",
            email="deleted@test.com",
            deleted_at=datetime.now(UTC),
        )
        async_session.add_all([active_user, deleted_user])
        await async_session.commit()

        active_mentor = MentorProfile(user_id=active_user.id)
        deleted_mentor = MentorProfile(user_id=deleted_user.id)
        async_session.add_all([active_mentor, deleted_mentor])
        await async_session.commit()

        async_session.add(
            MentorTopic(mentor_profile_id=active_mentor.id, topic_id=topic.id)
        )
        async_session.add(
            MentorTopic(mentor_profile_id=deleted_mentor.id, topic_id=topic.id)
        )
        await async_session.commit()

        from app.services.topic_service import get_mentors_for_topic

        mentors, total = await get_mentors_for_topic(async_session, topic.id)

        assert total == 1


class TestSearchTopics:
    """Tests for GET /api/topics/search."""

    async def test_search_finds_matching_topics(
        self, async_session: AsyncSession
    ) -> None:
        """Trigram search finds topics with similar names."""
        await async_session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await async_session.commit()

        async_session.add(Topic(name="Python Programming"))
        async_session.add(Topic(name="JavaScript"))
        async_session.add(Topic(name="Data Science"))
        await async_session.commit()

        from app.services.topic_service import search_topics

        results = await search_topics(async_session, "Python")

        assert len(results) >= 1
        names = [t.name for t, _ in results]
        assert "Python Programming" in names

    async def test_search_returns_similarity_scores(
        self, async_session: AsyncSession
    ) -> None:
        """Search results include similarity scores."""
        await async_session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await async_session.commit()

        async_session.add(Topic(name="Machine Learning"))
        await async_session.commit()

        from app.services.topic_service import search_topics

        results = await search_topics(async_session, "Machine")

        assert len(results) >= 1
        _, similarity = results[0]
        assert 0.0 <= similarity <= 1.0

    async def test_search_empty_query_returns_empty(
        self, async_session: AsyncSession
    ) -> None:
        """Empty search query returns no results."""
        from app.services.topic_service import search_topics

        results = await search_topics(async_session, "   ")

        assert results == []

    async def test_search_respects_limit(self, async_session: AsyncSession) -> None:
        """Search respects the limit parameter."""
        await async_session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await async_session.commit()

        for i in range(10):
            async_session.add(Topic(name=f"Test Topic {i}"))
        await async_session.commit()

        from app.services.topic_service import search_topics

        results = await search_topics(async_session, "Test", limit=3)

        assert len(results) <= 3
