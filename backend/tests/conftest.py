"""Shared test fixtures for SkillSwap tests.

This module provides fixtures for:
- Authentication testing (mocked JWKS, JWT generation)
- Database testing (async sessions with transaction rollback)
"""

import base64
import time
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.main import app

# =============================================================================
# DATABASE FIXTURES
# =============================================================================


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session that rolls back after each test.

    Each test runs in its own transaction that is rolled back at the end.
    This provides test isolation without permanently modifying the database.

    The pattern:
    1. Create a fresh engine for this test
    2. Begin a transaction on the connection
    3. Create a session bound to that connection
    4. Run the test
    5. Rollback the transaction (undoing all changes)
    6. Dispose of the engine
    """
    # Create engine for this test
    engine = create_async_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        echo=False,
    )

    async with engine.connect() as connection:
        # Begin a transaction that we'll rollback after the test
        await connection.begin()

        # Create a session bound to this connection
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            yield session

        # Rollback - undoes everything the test did
        await connection.rollback()

    # Clean up engine
    await engine.dispose()


# =============================================================================
# AUTHENTICATION FIXTURES
# =============================================================================


@pytest.fixture
def rsa_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate an RSA keypair for signing test tokens."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def test_kid() -> str:
    """Key ID for our test keypair."""
    return "test-key-id-12345"


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with fake Cognito configuration."""
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        cognito_region="us-west-2",
        cognito_user_pool_id="us-west-2_TestPool",
        cognito_app_client_id="test-client-id-abc123",
    )


def _int_to_base64url(n: int) -> str:
    """Convert an integer to base64url encoding (for JWK)."""
    byte_length = (n.bit_length() + 7) // 8
    n_bytes = n.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("ascii")


@pytest.fixture
def mock_jwk(
    rsa_keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    test_kid: str,
) -> dict[str, Any]:
    """Create a JWK from the test public key."""
    _, public_key = rsa_keypair
    public_numbers = public_key.public_numbers()

    return {
        "kty": "RSA",
        "kid": test_kid,
        "use": "sig",
        "alg": "RS256",
        "n": _int_to_base64url(public_numbers.n),
        "e": _int_to_base64url(public_numbers.e),
    }


@pytest.fixture
def private_key_pem(
    rsa_keypair: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
) -> bytes:
    """Get the private key in PEM format for signing tokens."""
    private_key, _ = rsa_keypair
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


@pytest.fixture
def make_token(
    private_key_pem: bytes,
    test_kid: str,
    test_settings: Settings,
) -> Callable[..., str]:
    """Factory fixture to create signed JWTs with customizable claims."""

    def _make_token(
        sub: str = "test-user-uuid-12345",
        token_use: str = "access",
        client_id: str | None = None,
        issuer: str | None = None,
        exp_offset: int = 3600,  # seconds from now
        kid: str | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = int(time.time())

        claims = {
            "sub": sub,
            "iss": issuer or test_settings.cognito_issuer,
            "token_use": token_use,
            "client_id": client_id or test_settings.cognito_app_client_id,
            "exp": now + exp_offset,
            "iat": now,
            "username": "testuser@example.com",
        }

        if extra_claims:
            claims.update(extra_claims)

        headers = {"kid": kid if kid is not None else test_kid}

        token: str = jwt.encode(
            claims,
            private_key_pem,
            algorithm="RS256",
            headers=headers,
        )
        return token

    return _make_token


@pytest.fixture
def mock_jwks_cache(
    mock_jwk: dict[str, Any], test_kid: str
) -> Generator[MagicMock, None, None]:
    """Patch jwks_cache.get_key to return our test JWK."""

    async def mock_get_key(kid: str) -> dict[str, Any]:
        if kid == test_kid:
            return mock_jwk
        raise KeyError(f"Key ID '{kid}' not found in JWKS")

    with patch("app.core.auth.jwks_cache") as mock_cache:
        mock_cache.get_key = AsyncMock(side_effect=mock_get_key)
        yield mock_cache


@pytest.fixture
def mock_settings_dep(test_settings: Settings) -> Generator[Settings, None, None]:
    """Patch get_settings to return test configuration."""
    with (
        patch("app.core.auth.get_settings", return_value=test_settings),
        patch("app.core.security.get_settings", return_value=test_settings),
    ):
        yield test_settings


@pytest.fixture
def client(mock_jwks_cache: MagicMock, mock_settings_dep: Settings) -> TestClient:
    """Test client with mocked auth dependencies."""
    return TestClient(app)
