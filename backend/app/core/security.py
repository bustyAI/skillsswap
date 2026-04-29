"""JWKS (JSON Web Key Set) caching and JWT utilities.

This module handles fetching and caching Cognito's public keys used
to verify JWT signatures. Keys are cached in memory and refreshed
every 24 hours.
"""

from datetime import datetime, timedelta
from typing import Any

import httpx

from app.core.config import get_settings


class JWKSCache:
    """In-memory cache for Cognito JWKS (public keys).

    Cognito publishes its public keys at a well-known URL. We fetch these
    keys and cache them to avoid hitting the network on every request.

    The cache refreshes every 24 hours. If a token arrives with an unknown
    key ID (kid), we also trigger a refresh in case Cognito rotated keys.

    Attributes:
        _keys: Dictionary mapping key ID (kid) to the full key dict.
        _last_refresh: When we last fetched from Cognito.
        _refresh_interval: How long to cache keys (24 hours).
    """

    def __init__(self, refresh_interval: timedelta = timedelta(hours=24)) -> None:
        self._keys: dict[str, dict[str, Any]] = {}
        self._last_refresh: datetime | None = None
        self._refresh_interval = refresh_interval

    def _is_stale(self) -> bool:
        """Check if the cache needs refreshing."""
        if self._last_refresh is None:
            return True
        return datetime.now() - self._last_refresh > self._refresh_interval

    async def refresh(self) -> None:
        """Fetch fresh JWKS from Cognito.

        This makes an HTTP request to the Cognito JWKS endpoint and
        updates our local cache with the returned keys.
        """
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.cognito_jwks_url)
            response.raise_for_status()
            jwks = response.json()

        # Index keys by their key ID (kid) for fast lookup
        self._keys = {key["kid"]: key for key in jwks["keys"]}
        self._last_refresh = datetime.now()

    async def get_key(self, kid: str) -> dict[str, Any]:
        """Get a public key by its key ID.

        If the cache is stale or the key isn't found, triggers a refresh.
        After refresh, if key still not found, raises KeyError.

        Args:
            kid: The key ID from the JWT header.
        Returns:
            The full JWK dict containing the public key material.
        Raises:
            KeyError: If the key ID isn't in the JWKS after refresh.
        """
        # Refresh if stale
        if self._is_stale():
            await self.refresh()

        # Try to get the key
        if kid in self._keys:
            return self._keys[kid]

        # Key not found - maybe Cognito rotated keys, try one refresh
        await self.refresh()
        if kid in self._keys:
            return self._keys[kid]

        raise KeyError(f"Key ID '{kid}' not found in JWKS")

    def clear(self) -> None:
        """Clear the cache. Useful for testing."""
        self._keys = {}
        self._last_refresh = None


# This is created once and reused throughout the application
jwks_cache = JWKSCache()
