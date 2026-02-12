"""Tests for auth utilities and rate limiter middleware."""

import pytest

from api.v1.auth import create_token, verify_token
from api.v1.middleware import RateLimiter


# ===== AUTH TOKEN TESTS =====


class TestAuth:
    def test_create_and_verify_token(self):
        """A freshly created token should verify successfully."""
        secret = "test-secret-key"
        token = create_token(
            tenant_id="tenant-1",
            role="admin",
            secret=secret,
        )
        payload = verify_token(token, secret)
        assert payload is not None
        assert payload["tenant_id"] == "tenant-1"
        assert payload["role"] == "admin"

    def test_invalid_secret_fails(self):
        """A token verified with the wrong secret should return None."""
        token = create_token(
            tenant_id="tenant-1",
            role="admin",
            secret="correct-secret",
        )
        result = verify_token(token, "wrong-secret")
        assert result is None

    def test_expired_token_fails(self):
        """A token with expires_hours=0 should be expired immediately."""
        secret = "test-secret"
        token = create_token(
            tenant_id="tenant-1",
            role="viewer",
            secret=secret,
            expires_hours=0,
        )
        result = verify_token(token, secret)
        assert result is None


# ===== RATE LIMITER TESTS =====


class TestRateLimiter:
    def test_allows_within_limit(self):
        """Requests within the limit should be allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("tenant-1") is True

    def test_blocks_over_limit(self):
        """Requests exceeding the limit should be blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("tenant-1")
        assert limiter.check("tenant-1") is False
