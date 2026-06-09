"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Pydantic Settings automatically reads from environment variables
    and .env files. All values are validated at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str
    redis_url: str

    # AWS Cognito
    cognito_region: str
    cognito_user_pool_id: str
    cognito_app_client_id: str

    # Admin user IDs (comma-separated Cognito subs)
    admin_user_ids: str = ""

    @property
    def admin_user_ids_set(self) -> set[str]:
        """Parse admin IDs into a set for O(1) lookup."""
        if not self.admin_user_ids:
            return set()
        return {uid.strip() for uid in self.admin_user_ids.split(",") if uid.strip()}

    @property
    def cognito_jwks_url(self) -> str:
        """JWKS endpoint URL computed from region and pool ID.

        This is where Cognito publishes the public keys used to verify JWTs.
        The URL follows a standard pattern for all Cognito user pools.
        """
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}/.well-known/jwks.json"
        )

    @property
    def cognito_issuer(self) -> str:
        """Expected JWT issuer claim.

        Cognito tokens include an 'iss' claim that must match this value.
        We validate this to ensure tokens came from our specific user pool.
        """
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Using lru_cache ensures we only parse environment variables once.
    The settings object is then reused for all subsequent calls.
    """
    return Settings()
