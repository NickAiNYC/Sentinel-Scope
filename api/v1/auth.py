"""Simple JWT-like auth utilities using only the standard library."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from enum import StrEnum


class Role(StrEnum):
    """Authorization roles for API access."""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    AUDITOR = "auditor"
    VIEWER = "viewer"


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """URL-safe base64 decode with padding restoration."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(payload_b64: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature over the encoded payload."""
    sig = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(sig)


def create_token(
    tenant_id: str,
    role: str,
    secret: str,
    expires_hours: int = 24,
) -> str:
    """Create a base64-encoded JSON token with HMAC-SHA256 signature.

    Format: ``<payload_b64>.<signature_b64>``
    """
    now = time.time()
    payload = {
        "tenant_id": tenant_id,
        "role": role,
        "iat": int(now),
        "exp": int(now + expires_hours * 3600),
    }
    payload_b64 = _b64url_encode(json.dumps(payload).encode("utf-8"))
    signature = _sign(payload_b64, secret)
    return f"{payload_b64}.{signature}"


def verify_token(token: str, secret: str) -> dict | None:
    """Verify signature and expiry. Returns payload dict or ``None``."""
    parts = token.split(".")
    if len(parts) != 2:
        return None

    payload_b64, signature = parts

    expected_sig = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected_sig):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (json.JSONDecodeError, Exception):
        return None

    if payload.get("exp", 0) < time.time():
        return None

    return payload
