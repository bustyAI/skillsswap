from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.dependencies import DbSession
from app.schemas.auth import TokenClaims
from app.schemas.meeting import (
    MeetingListResponse,
    MeetingResponse,
    MeetingSchedule,
    MeetingWithUsersResponse,
)
from app.schemas.mentorship import UserBrief
from app.schemas.review import ReviewCreate, ReviewerBrief, ReviewResponse, ReviewUpdate
from app.services.meeting_service import (
    InvalidMeetingTransitionError,
    InvalidMeetingURLError,
    MeetingNotYetScheduledTimeError,
    NotPartyToMeetingError,
    OnlyMentorCanScheduleError,
    cancel_meeting,
    complete_meeting,
    get_meeting_by_id,
    list_user_meetings,
    schedule_meeting,
)
from app.services.review_service import (
    MeetingNotCompletedError,
    OnlyMenteeCanReviewError,
    ReviewAlreadyExistsError,
    ReviewEditWindowExpiredError,
    create_review,
    get_review_by_meeting_id,
    update_review,
)
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _build_response(meeting) -> MeetingResponse:  # type: ignore[no-untyped-def]
    return MeetingResponse(
        id=meeting.id,
        mentorship_id=meeting.mentorship_id,
        scheduled_time=meeting.scheduled_time,
        meeting_url=meeting.meeting_url,
        status=meeting.status,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def _build_response_with_users(meeting) -> MeetingWithUsersResponse:  # type: ignore[no-untyped-def]
    mentorship = meeting.mentorship
    return MeetingWithUsersResponse(
        id=meeting.id,
        mentorship_id=meeting.mentorship_id,
        scheduled_time=meeting.scheduled_time,
        meeting_url=meeting.meeting_url,
        status=meeting.status,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        mentor=UserBrief.model_validate(mentorship.mentor)
        if mentorship.mentor
        else None,
        mentee=UserBrief.model_validate(mentorship.mentee)
        if mentorship.mentee
        else None,
    )


@router.get("/me", response_model=MeetingListResponse)
async def get_my_meetings(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MeetingListResponse:
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

    meetings = await list_user_meetings(db, user, upcoming_only=True)
    return MeetingListResponse(
        meetings=[_build_response_with_users(m) for m in meetings]
    )


@router.post("/{meeting_id}/schedule", response_model=MeetingResponse)
async def schedule_meeting_endpoint(
    meeting_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: MeetingSchedule,
) -> MeetingResponse:
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

    meeting = await get_meeting_by_id(db, meeting_id, include_mentorship=True)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    try:
        meeting = await schedule_meeting(
            db, meeting, user, data.scheduled_time, data.meeting_url
        )
    except OnlyMentorCanScheduleError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidMeetingTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except InvalidMeetingURLError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(meeting)


@router.post("/{meeting_id}/cancel", response_model=MeetingResponse)
async def cancel_meeting_endpoint(
    meeting_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MeetingResponse:
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

    meeting = await get_meeting_by_id(db, meeting_id, include_mentorship=True)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    try:
        meeting = await cancel_meeting(db, meeting, user)
    except NotPartyToMeetingError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidMeetingTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(meeting)


@router.post("/{meeting_id}/complete", response_model=MeetingResponse)
async def complete_meeting_endpoint(
    meeting_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> MeetingResponse:
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

    meeting = await get_meeting_by_id(db, meeting_id, include_mentorship=True)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    try:
        meeting = await complete_meeting(db, meeting, user)
    except NotPartyToMeetingError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except InvalidMeetingTransitionError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except MeetingNotYetScheduledTimeError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_response(meeting)


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


@router.post(
    "/{meeting_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting_review(
    meeting_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: ReviewCreate,
) -> ReviewResponse:
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

    meeting = await get_meeting_by_id(db, meeting_id, include_mentorship=True)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    try:
        review = await create_review(db, meeting, user, data.rating, data.comment)
    except MeetingNotCompletedError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except OnlyMenteeCanReviewError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except ReviewAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err

    return _build_review_response(review)


@router.patch("/{meeting_id}/review", response_model=ReviewResponse)
async def update_meeting_review(
    meeting_id: UUID,
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
    data: ReviewUpdate,
) -> ReviewResponse:
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

    review = await get_review_by_meeting_id(db, meeting_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    try:
        review = await update_review(db, review, user, data.rating, data.comment)
    except OnlyMenteeCanReviewError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
    except ReviewEditWindowExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return _build_review_response(review)
