"""FastAPI authentication dependencies.

This module provides the `get_current_user` dependency that validates
Cognito JWTs and extracts user claims. Use it to protect routes:

    @router.get("/protected")
    async def protected_route(user: TokenClaims = Depends(get_current_user)):
        return {"user_id": user.sub}
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.security import jwks_cache
from app.schemas.auth import TokenClaims

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
# auto_error=True means it returns 403 if header is missing
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenClaims:
    """Validate JWT and return decoded claims.

    This is a FastAPI dependency that:
    1. Extracts the Bearer token from the Authorization header
    2. Decodes the JWT header to find the key ID (kid)
    3. Fetches the public key from our JWKS cache
    4. Verifies the signature and standard claims
    5. Returns the validated claims as TokenClaims

    Args:
        credentials: Automatically injected by FastAPI from the
            Authorization header.

    Returns:
        TokenClaims with the decoded and validated JWT claims.

    Raises:
        HTTPException: 401 if token is invalid, expired, or malformed.
    """
    token = credentials.credentials
    settings = get_settings()

    # First, decode the header without verification to get the key ID
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token header missing 'kid'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch the public key from cache
    try:
        jwk = await jwks_cache.get_key(kid)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown signing key: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        # Network error fetching JWKS
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not fetch signing keys: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Verify the token signature and claims
    try:
        payload = jwt.decode(
            token,
            jwk,
            algorithms=["RS256"],
            issuer=settings.cognito_issuer,
            # Cognito access tokens use client_id claim, not aud
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Verify token_use is "access" (not "id" token)
    if payload.get("token_use") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token_use, expected 'access'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify client_id matches our app
    if payload.get("client_id") != settings.cognito_app_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token was not issued for this application",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return validated claims as Pydantic model
    return TokenClaims(
        sub=payload["sub"],
        iss=payload["iss"],
        token_use=payload["token_use"],
        exp=payload["exp"],
        iat=payload["iat"],
        client_id=payload["client_id"],
        username=payload.get("username"),
    )
