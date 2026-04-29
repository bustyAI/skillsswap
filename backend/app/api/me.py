"""Current user endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.auth import TokenClaims

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=TokenClaims)
async def get_me(
    current_user: Annotated[TokenClaims, Depends(get_current_user)],
) -> TokenClaims:
    """Return the current authenticated user's token claims.

    This endpoint requires a valid Cognito access token in the
    Authorization header. It returns the decoded JWT claims,
    which includes the user's unique ID (sub), token metadata,
    and other Cognito-provided information.

    Use this endpoint to:
    - Verify a token is valid
    - Get the current user's ID for client-side use
    - Debug authentication issues
    """
    return current_user
