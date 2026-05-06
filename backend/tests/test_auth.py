"""Tests for JWT validation and the /api/me endpoint."""

from collections.abc import Callable

from fastapi.testclient import TestClient


class TestValidToken:
    """Tests for valid token acceptance."""

    def test_valid_token_returns_claims(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A properly signed token with valid claims should return user info."""
        token = make_token(sub="user-uuid-12345")

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == "user-uuid-12345"
        assert data["token_use"] == "access"
        assert "exp" in data
        assert "iat" in data

    def test_valid_token_includes_username(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """Token claims should include optional username field."""
        token = make_token()

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser@example.com"


class TestExpiredToken:
    """Tests for expired token rejection."""

    def test_expired_token_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """An expired token should be rejected with 401."""
        # Create token that expired 1 hour ago
        token = make_token(exp_offset=-3600)

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers


class TestMalformedToken:
    """Tests for malformed token rejection."""

    def test_completely_invalid_token_returns_401(
        self,
        client: TestClient,
    ) -> None:
        """A completely invalid token string should be rejected."""
        response = client.get(
            "/api/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )

        assert response.status_code == 401

    def test_truncated_token_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A truncated token should be rejected."""
        token = make_token()
        truncated = token[:50]  # Cut off most of the token

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {truncated}"},
        )

        assert response.status_code == 401

    def test_tampered_signature_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A token with tampered signature should be rejected."""
        token = make_token()
        # Tamper with the last character of the signature
        parts = token.rsplit(".", 1)
        tampered = (
            parts[0] + "." + parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        )

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {tampered}"},
        )

        assert response.status_code == 401


class TestWrongIssuer:
    """Tests for wrong issuer rejection."""

    def test_wrong_issuer_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A token from a different issuer should be rejected."""
        token = make_token(
            issuer="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_WrongPool"
        )

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "validation failed" in response.json()["detail"].lower()


class TestWrongClientId:
    """Tests for wrong client_id rejection."""

    def test_wrong_client_id_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A token issued for a different app client should be rejected."""
        token = make_token(client_id="wrong-client-id-xyz")

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "not issued for this application" in response.json()["detail"]


class TestWrongTokenUse:
    """Tests for wrong token_use rejection."""

    def test_id_token_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """An ID token (instead of access token) should be rejected."""
        token = make_token(token_use="id")

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "token_use" in response.json()["detail"].lower()


class TestMissingKid:
    """Tests for missing key ID in token header."""

    def test_missing_kid_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A token without a kid in the header should be rejected."""
        # Create a token manually without kid
        # We pass empty string kid which our fixture handles specially
        import time

        from jose import jwt

        from app.core.config import Settings

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
            redis_url="redis://localhost:6379/0",
            cognito_region="us-west-2",
            cognito_user_pool_id="us-west-2_TestPool",
            cognito_app_client_id="test-client-id-abc123",
        )

        # We need to create a token without kid - use HS256 for simplicity
        # since we're testing header parsing, not signature verification
        now = int(time.time())
        claims = {
            "sub": "test-user",
            "iss": settings.cognito_issuer,
            "token_use": "access",
            "client_id": settings.cognito_app_client_id,
            "exp": now + 3600,
            "iat": now,
        }

        # Create token with no kid in header
        # python-jose doesn't allow removing kid easily with RS256,
        # so we craft a header without it using HS256 (will fail signature anyway)
        token = jwt.encode(claims, "secret", algorithm="HS256")

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "kid" in response.json()["detail"].lower()


class TestUnknownKid:
    """Tests for unknown key ID rejection."""

    def test_unknown_kid_returns_401(
        self,
        client: TestClient,
        make_token: Callable[..., str],
    ) -> None:
        """A token with an unknown key ID should be rejected."""
        token = make_token(kid="unknown-key-id-99999")

        response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "unknown signing key" in response.json()["detail"].lower()


class TestMissingAuth:
    """Tests for missing authentication."""

    def test_no_auth_header_returns_401(
        self,
        client: TestClient,
    ) -> None:
        """A request without Authorization header should return 401."""
        response = client.get("/api/me")

        assert response.status_code == 401

    def test_empty_bearer_returns_401(
        self,
        client: TestClient,
    ) -> None:
        """An empty Bearer token should return 401."""
        response = client.get(
            "/api/me",
            headers={"Authorization": "Bearer "},
        )

        assert response.status_code == 401


class TestHealthEndpoint:
    """Verify health endpoint doesn't require auth."""

    def test_health_no_auth_required(
        self,
        client: TestClient,
    ) -> None:
        """The health endpoint should work without authentication."""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
