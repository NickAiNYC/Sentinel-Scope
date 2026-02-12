"""Permit lifecycle state machine for construction permitting workflows."""

from __future__ import annotations

from enum import StrEnum


class PermitStage(StrEnum):
    """Lifecycle stages a construction permit may occupy."""

    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CLOSED = "closed"


class PermitLifecycle:
    """Jurisdiction-agnostic permit lifecycle state machine.

    Defines valid stage transitions and exposes helpers for workflow
    engines and UI guards.
    """

    TRANSITIONS: dict[PermitStage, list[PermitStage]] = {
        PermitStage.APPLIED: [
            PermitStage.UNDER_REVIEW,
        ],
        PermitStage.UNDER_REVIEW: [
            PermitStage.APPROVED,
            PermitStage.CLOSED,
        ],
        PermitStage.APPROVED: [
            PermitStage.ACTIVE,
            PermitStage.CLOSED,
        ],
        PermitStage.ACTIVE: [
            PermitStage.SUSPENDED,
            PermitStage.EXPIRED,
            PermitStage.REVOKED,
            PermitStage.CLOSED,
        ],
        PermitStage.SUSPENDED: [
            PermitStage.ACTIVE,
            PermitStage.REVOKED,
            PermitStage.CLOSED,
        ],
        PermitStage.EXPIRED: [
            PermitStage.CLOSED,
        ],
        PermitStage.REVOKED: [
            PermitStage.CLOSED,
        ],
        PermitStage.CLOSED: [],
    }

    @classmethod
    def can_transition(cls, current: PermitStage, target: PermitStage) -> bool:
        """Return *True* if *target* is a valid successor of *current*."""
        return target in cls.TRANSITIONS.get(current, [])

    @classmethod
    def get_next_stages(cls, current: PermitStage) -> list[PermitStage]:
        """Return the list of stages reachable from *current*."""
        return list(cls.TRANSITIONS.get(current, []))
