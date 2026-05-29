"""Topic discovery endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.db.dependencies import DbSession
from app.schemas.topic import (
    MentorBriefResponse,
    TopicListResponse,
    TopicMentorsResponse,
    TopicResponse,
    TopicSearchResponse,
    TopicSearchResult,
)
from app.services.topic_service import (
    get_mentors_for_topic,
    get_topic_by_id,
    list_topics,
    search_topics,
)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
async def get_topics(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    parent_topic_id: UUID | None = None,
) -> TopicListResponse:
    """List topics with optional parent filter.

    When parent_topic_id is omitted, returns root-level topics only.
    """
    topics, total = await list_topics(
        db,
        page=page,
        page_size=page_size,
        parent_topic_id=parent_topic_id,
    )

    return TopicListResponse(
        items=[TopicResponse.model_validate(t) for t in topics],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/search", response_model=TopicSearchResponse)
async def search_topics_endpoint(
    db: DbSession,
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
) -> TopicSearchResponse:
    """Search topics by name using fuzzy matching."""
    results = await search_topics(db, query=q, limit=limit)

    return TopicSearchResponse(
        items=[
            TopicSearchResult(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                similarity=similarity,
            )
            for topic, similarity in results
        ],
        query=q,
    )


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    db: DbSession,
) -> TopicResponse:
    """Get a single topic by ID."""
    topic = await get_topic_by_id(db, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    return TopicResponse.model_validate(topic)


@router.get("/{topic_id}/mentors", response_model=TopicMentorsResponse)
async def get_topic_mentors(
    topic_id: UUID,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TopicMentorsResponse:
    """Get mentors for a topic, ordered by rating."""
    topic = await get_topic_by_id(db, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    mentors, total = await get_mentors_for_topic(
        db,
        topic_id=topic_id,
        page=page,
        page_size=page_size,
    )

    return TopicMentorsResponse(
        items=[MentorBriefResponse.model_validate(m) for m in mentors],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )
