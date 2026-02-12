"""Simple middleware utilities for tenant context and rate limiting."""

from __future__ import annotations

import time

from fastapi import Request


class TenantContext:
    """Extracts ``tenant_id`` from the ``X-Tenant-ID`` request header."""

    @staticmethod
    def extract(request: Request) -> str | None:
        """Return the tenant ID from the request, or ``None`` if absent."""
        return request.headers.get("X-Tenant-ID")


class RateLimiter:
    """In-memory token-bucket rate limiter keyed by tenant ID.

    Parameters
    ----------
    max_requests:
        Maximum number of requests allowed within *window_seconds*.
    window_seconds:
        Length of the sliding window in seconds.
    """

    def __init__(
        self, max_requests: int = 100, window_seconds: int = 60
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    def _cleanup(self, tenant_id: str) -> None:
        """Remove timestamps older than the current window."""
        cutoff = time.time() - self.window_seconds
        self._buckets[tenant_id] = [
            ts for ts in self._buckets.get(tenant_id, []) if ts > cutoff
        ]

    def check(self, tenant_id: str) -> bool:
        """Return ``True`` if the tenant is allowed to make a request."""
        self._cleanup(tenant_id)
        if len(self._buckets.get(tenant_id, [])) >= self.max_requests:
            return False
        self._buckets.setdefault(tenant_id, []).append(time.time())
        return True

    def get_retry_after(self, tenant_id: str) -> int:
        """Return seconds until the next request is allowed."""
        self._cleanup(tenant_id)
        timestamps = self._buckets.get(tenant_id, [])
        if len(timestamps) < self.max_requests:
            return 0
        oldest = min(timestamps)
        retry_after = self.window_seconds - (time.time() - oldest)
        return max(int(retry_after) + 1, 1)
