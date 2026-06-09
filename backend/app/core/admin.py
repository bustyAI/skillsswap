"""Admin authorization dependency.

For V1, admin status is determined by a hardcoded allowlist of Cognito
user IDs in the ADMIN_USER_IDS environment variable.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.schemas.auth import TokenClaims


async def require_admin(
    user: Annotated[TokenClaims, Depends(get_current_user)],
) -> TokenClaims:
    """Dependency that requires the current user to be an admin.

    Raises 403 Forbidden if the user is not in the admin allowlist.
    """
    settings = get_settings()
    if user.sub not in settings.admin_user_ids_set:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


AdminUser = Annotated[TokenClaims, Depends(require_admin)]
