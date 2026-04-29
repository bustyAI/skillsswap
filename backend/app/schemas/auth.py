"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field


class TokenClaims(BaseModel):
    """Decoded JWT claims from a Cognito access token.

    These are the standard claims present in Cognito access tokens.
    We extract and validate these during authentication.

    Attributes:
        sub: The user's unique identifier (UUID) in Cognito. This becomes
            our user_id throughout the application.
        iss: Token issuer - must match our Cognito user pool URL.
        aud: Audience - for access tokens, this is "aws.cognito.signin.user.admin"
             or may not be present (client_id is in other claims).
        token_use: Must be "access" for access tokens.
        exp: Token expiration timestamp (Unix epoch seconds).
        iat: Token issued-at timestamp (Unix epoch seconds).
        client_id: The Cognito app client that issued this token.
        username: The user's username (often same as email for email-based auth).
    """

    sub: str = Field(..., description="User's unique identifier (UUID)")
    iss: str = Field(..., description="Token issuer URL")
    token_use: str = Field(..., description="Token type, must be 'access'")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued-at timestamp")
    client_id: str = Field(..., description="Cognito app client ID")
    username: str | None = Field(None, description="User's username")

    @property
    def user_id(self) -> str:
        """Alias for sub - the user's unique identifier.

        Throughout the application, we refer to the Cognito 'sub' claim
        as 'user_id' for clarity.
        """
        return self.sub
