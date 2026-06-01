"""Mentorship lifecycle endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.db.dependencies import DbSession
from app.db.models.mentorship import MentorshipStatus
from app.schemas.auth import TokenClaims
from app.schemas.mentorship import (
    MentorshipCreate,
    MentorshipListResponse,
    MentorshipResponse,
    UserBrief,
)
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
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/mentorships", tags=["mentorships"])


def _build_response(mentorship) -> MentorshipResponse:  # type: ignore[no-untyped-def]
    return MentorshipResponse(
        id=mentorship.id,
        mentor_id=mentorship.mentor_id,
        mentee_id=mentorship.mentee_id,
        status=mentorship.status,
        created_at=mentorship.created_at,
        updated_at=mentorship.updated_at,
        mentor=UserBrief.model_validate(mentorship.mentor)
        if mentorship.mentor
        else None,
        mentee=UserBrief.model_validate(mentorship.mentee)
        if mentorship.mentee
        else None,
    )


@router.post("", response_model=MentorshipResponse, status_code=status.HTTP_201_CREATED)
async def request_mentorship(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: MentorshipCreate,
) -> MentorshipResponse:
    """Request a mentorship with a mentor.

    Creates a new mentorship in REQUESTED status. The mentee is the
    current authenticated user.
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
        mentorship = await create_mentorship(db, user, data.mentor_id)
    except SelfMentorshipError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except MentorNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except DuplicateMentorshipError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err

    return _build_response(mentorship)


@router.get("/me", response_model=MentorshipListResponse)
async def get_my_mentorships(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    status_filter: Annotated[MentorshipStatus | None, Query(alias="status")] = None,
) -> MentorshipListResponse:
    """Get all mentorships for the current user.

    Returns mentorships where user is either mentor or mentee.
    Optional status filter.
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

    mentorships = await list_user_mentorships(db, user, status_filter=status_filter)
    return MentorshipListResponse(mentorships=[_build_response(m) for m in mentorships])


@router.get("/{mentorship_id}", response_model=MentorshipResponse)
async def get_mentorship(
    mentorship_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorshipResponse:
    """Get a specific mentorship by ID.

    Only accessible by parties to the mentorship.
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

    mentorship = await get_mentorship_by_id(db, mentorship_id, include_users=True)
    if mentorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship not found",
        )

    if user.id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this mentorship",
        )

    return _build_response(mentorship)


@router.post("/{mentorship_id}/accept", response_model=MentorshipResponse)
async def accept_mentorship_request(
    mentorship_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorshipResponse:
    """Accept a mentorship request (mentor only).

    Transitions mentorship from REQUESTED to ACTIVE.
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

    mentorship = await get_mentorship_by_id(db, mentorship_id, include_users=True)
    if mentorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship not found",
        )

    try:
        mentorship = await accept_mentorship(db, mentorship, user)
    except NotPartyToMentorshipError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidStatusTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(mentorship)


@router.post("/{mentorship_id}/decline", response_model=MentorshipResponse)
async def decline_mentorship_request(
    mentorship_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorshipResponse:
    """Decline a mentorship request (mentor only).

    Transitions mentorship from REQUESTED to DECLINED.
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

    mentorship = await get_mentorship_by_id(db, mentorship_id, include_users=True)
    if mentorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship not found",
        )

    try:
        mentorship = await decline_mentorship(db, mentorship, user)
    except NotPartyToMentorshipError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidStatusTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(mentorship)


@router.post("/{mentorship_id}/end", response_model=MentorshipResponse)
async def end_mentorship_relationship(
    mentorship_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MentorshipResponse:
    """End an active mentorship (either party).

    Transitions mentorship from ACTIVE to ENDED.
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

    mentorship = await get_mentorship_by_id(db, mentorship_id, include_users=True)
    if mentorship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship not found",
        )

    try:
        mentorship = await end_mentorship(db, mentorship, user)
    except NotPartyToMentorshipError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidStatusTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(mentorship)
