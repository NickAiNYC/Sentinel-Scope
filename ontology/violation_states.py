"""Violation state machine for compliance enforcement workflows."""

from __future__ import annotations

from enum import StrEnum


class ViolationState(StrEnum):
    """Lifecycle states a violation may occupy."""

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    UNDER_REVIEW = "under_review"
    CURE_PERIOD = "cure_period"
    HEARING_SCHEDULED = "hearing_scheduled"
    HEARING_COMPLETED = "hearing_completed"
    PENALIZED = "penalized"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    APPEALED = "appealed"


class ViolationStateMachine:
    """Jurisdiction-agnostic violation state machine.

    Defines which state transitions are legally valid and exposes helpers
    for workflow engines and UI guards.
    """

    TRANSITIONS: dict[ViolationState, list[ViolationState]] = {
        ViolationState.REPORTED: [
            ViolationState.ACKNOWLEDGED,
            ViolationState.DISMISSED,
        ],
        ViolationState.ACKNOWLEDGED: [
            ViolationState.UNDER_REVIEW,
            ViolationState.CURE_PERIOD,
        ],
        ViolationState.UNDER_REVIEW: [
            ViolationState.CURE_PERIOD,
            ViolationState.HEARING_SCHEDULED,
            ViolationState.DISMISSED,
        ],
        ViolationState.CURE_PERIOD: [
            ViolationState.RESOLVED,
            ViolationState.HEARING_SCHEDULED,
        ],
        ViolationState.HEARING_SCHEDULED: [
            ViolationState.HEARING_COMPLETED,
        ],
        ViolationState.HEARING_COMPLETED: [
            ViolationState.PENALIZED,
            ViolationState.DISMISSED,
        ],
        ViolationState.PENALIZED: [
            ViolationState.RESOLVED,
            ViolationState.APPEALED,
        ],
        ViolationState.RESOLVED: [],
        ViolationState.DISMISSED: [],
        ViolationState.APPEALED: [
            ViolationState.HEARING_SCHEDULED,
            ViolationState.RESOLVED,
            ViolationState.PENALIZED,
        ],
    }

    @classmethod
    def can_transition(cls, current: ViolationState, target: ViolationState) -> bool:
        """Return *True* if *target* is a valid successor of *current*."""
        return target in cls.TRANSITIONS.get(current, [])

    @classmethod
    def get_next_states(cls, current: ViolationState) -> list[ViolationState]:
        """Return the list of states reachable from *current*."""
        return list(cls.TRANSITIONS.get(current, []))
