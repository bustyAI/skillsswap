"""User profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.dependencies import DbSession
from app.schemas.auth import TokenClaims
from app.schemas.user import UserResponse
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
    db: DbSession,
) -> UserResponse:
    """Return the current user's profile.

    Uses just-in-time provisioning: if this is the user's first request,
    a User record is created automatically from their Cognito identity.
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

    return UserResponse.model_validate(user)
