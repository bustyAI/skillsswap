"""Mentor profile endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.core.auth import get_current_user
from app.db.dependencies import DbSession
from app.schemas.auth import TokenClaims
from app.schemas.mentor_profile import (
    MentorProfileCreate,
    MentorProfileResponse,
    MentorProfileUpdate,
    MentorTopicsResponse,
    MentorTopicsUpdate,
    TopicBrief,
)
from app.schemas.review import ReviewerBrief, ReviewListResponse, ReviewResponse
from app.services.mentor_service import (
    create_mentor_profile,
    get_mentor_profile_by_user_id,
    get_mentor_topics,
    replace_mentor_topics,
    update_mentor_profile,
)
from app.services.review_service import list_mentor_reviews
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/mentors", tags=["mentors"])


# NOTE: /me routes MUST be defined before /{user_id} routes
# otherwise FastAPI will try to parse "me" as a UUID


@router.get("/me", response_model=MentorProfileResponse)
async def get_my_mentor_profile(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorProfileResponse:
    """Get the current user's mentor profile.

    Returns 404 if the user doesn't have a mentor profile.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    mentor_profile = await get_mentor_profile_by_user_id(db, user.id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )
    return MentorProfileResponse.model_validate(mentor_profile)


@router.post(
    "/me", response_model=MentorProfileResponse, status_code=status.HTTP_201_CREATED
)
async def create_my_mentor_profile(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: MentorProfileCreate,
) -> MentorProfileResponse:
    """Create a mentor profile for the current user.

    Returns 409 if the user already has a mentor profile.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    try:
        mentor_profile = await create_mentor_profile(db, user, data)
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mentor profile already exists",
        ) from err

    return MentorProfileResponse.model_validate(mentor_profile)


@router.patch("/me", response_model=MentorProfileResponse)
async def update_my_mentor_profile(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: MentorProfileUpdate,
) -> MentorProfileResponse:
    """Update the current user's mentor profile.

    Returns 404 if the user doesn't have a mentor profile.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    mentor_profile = await get_mentor_profile_by_user_id(db, user.id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    updated_profile = await update_mentor_profile(db, mentor_profile, data)
    return MentorProfileResponse.model_validate(updated_profile)


@router.get("/me/topics", response_model=MentorTopicsResponse)
async def get_my_mentor_topics(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorTopicsResponse:
    """Get the current user's mentor topic list.

    Returns 404 if the user doesn't have a mentor profile.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    mentor_profile = await get_mentor_profile_by_user_id(db, user.id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    topics = await get_mentor_topics(db, mentor_profile)
    return MentorTopicsResponse(topics=[TopicBrief.model_validate(t) for t in topics])


@router.post("/me/topics", response_model=MentorTopicsResponse)
async def replace_my_mentor_topics(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: MentorTopicsUpdate,
) -> MentorTopicsResponse:
    """Replace the current user's mentor topic list.

    Removes all existing topic associations and creates new ones
    for the provided topic IDs. Invalid topic IDs are silently ignored.

    Returns 404 if the user doesn't have a mentor profile.
    """
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing username claim",
        )

    user = await get_or_create_user(
        db=db,
        cognito_sub=current_user.sub,
        email=current_user.username,
    )

    mentor_profile = await get_mentor_profile_by_user_id(db, user.id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    topics = await replace_mentor_topics(db, mentor_profile, data.topic_ids)
    return MentorTopicsResponse(topics=[TopicBrief.model_validate(t) for t in topics])


# /{user_id} routes MUST come after /me routes


@router.get("/{user_id}", response_model=MentorProfileResponse)
async def get_mentor_by_user_id(
    user_id: UUID,
    db: DbSession,
) -> MentorProfileResponse:
    """Get a mentor profile by user ID.

    This is a public endpoint - no authentication required.
    Returns 404 if the user doesn't have a mentor profile or is deleted.
    """
    mentor_profile = await get_mentor_profile_by_user_id(db, user_id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )
    return MentorProfileResponse.model_validate(mentor_profile)


@router.get("/{user_id}/topics", response_model=MentorTopicsResponse)
async def get_mentor_topics_by_user_id(
    user_id: UUID,
    db: DbSession,
) -> MentorTopicsResponse:
    """Get a mentor's topic list by user ID.

    This is a public endpoint - no authentication required.
    Returns 404 if the user doesn't have a mentor profile.
    """
    mentor_profile = await get_mentor_profile_by_user_id(db, user_id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    topics = await get_mentor_topics(db, mentor_profile)
    return MentorTopicsResponse(topics=[TopicBrief.model_validate(t) for t in topics])


def _build_review_response(review) -> ReviewResponse:  # type: ignore[no-untyped-def]
    return ReviewResponse(
        id=review.id,
        meeting_id=review.meeting_id,
        reviewer_id=review.reviewer_id,
        rating=review.rating,
        comment=review.comment,
        editable_until=review.editable_until,
        created_at=review.created_at,
        updated_at=review.updated_at,
        reviewer=ReviewerBrief.model_validate(review.reviewer)
        if review.reviewer
        else None,
    )


@router.get("/{user_id}/reviews", response_model=ReviewListResponse)
async def get_mentor_reviews(
    user_id: UUID,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReviewListResponse:
    mentor_profile = await get_mentor_profile_by_user_id(db, user_id)
    if mentor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    reviews, total = await list_mentor_reviews(db, user_id, page, page_size)
    return ReviewListResponse(
        reviews=[_build_review_response(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
    )
