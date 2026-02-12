"""Deterministic risk scoring engine for NYC DOB construction compliance."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from core.compliance_models import RiskAssessment

# Violation class severity points (higher = more severe)
_VIOLATION_CLASS_SCORES: dict[str, int] = {
    "Class C": 30,
    "Class B": 20,
    "Class A": 10,
}

# Fine schedule per violation class (USD)
_FINE_SCHEDULE: dict[str, float] = {
    "Class A": 2_500.0,
    "Class B": 10_000.0,
    "Class C": 25_000.0,
}

# Building-type base risk (residential occupants = higher life-safety risk)
_BUILDING_TYPE_RISK: dict[str, float] = {
    "residential": 1.0,
    "mixed": 0.7,
    "commercial": 0.4,
}

# NYC supertall threshold; height factor saturates at this story count.
_MAX_HEIGHT_STORIES = 40


def _sigmoid(x: float, midpoint: float, steepness: float = 0.15) -> float:
    """Standard sigmoid mapped to [0, 1]."""
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


class DeterministicRiskEngine:
    """Fully deterministic, reproducible risk scorer.

    Every numeric output is derived from explicit weights and formulas so
    that any two runs with identical inputs produce identical outputs.
    """

    def __init__(self, model_version: str = "1.0.0") -> None:
        self.model_version = model_version

    # ------------------------------------------------------------------
    # Component scorers (pure functions of their inputs)
    # ------------------------------------------------------------------

    @staticmethod
    def _violation_severity_score(violation_classes: list[str]) -> float:
        """0-30: highest severity class present."""
        if not violation_classes:
            return 0.0
        return float(
            max(_VIOLATION_CLASS_SCORES.get(vc, 0) for vc in violation_classes)
        )

    @staticmethod
    def _permit_age_score(permit_age_days: int) -> float:
        """0-15: linear ramp from 180 → 720 days."""
        if permit_age_days <= 180:
            return 0.0
        if permit_age_days >= 720:
            return 15.0
        return 15.0 * (permit_age_days - 180) / (720 - 180)

    @staticmethod
    def _inspection_failure_score(
        inspection_failures: int,
        inspection_total: int,
    ) -> float:
        """0-15: failure_rate × 15."""
        if inspection_total <= 0:
            return 0.0
        rate = min(inspection_failures / inspection_total, 1.0)
        return rate * 15.0

    @staticmethod
    def _schedule_delay_score(milestone_delay_days: int) -> float:
        """0-10: linear ramp from 0 → 90 days."""
        if milestone_delay_days <= 0:
            return 0.0
        if milestone_delay_days >= 90:
            return 10.0
        return 10.0 * milestone_delay_days / 90.0

    @staticmethod
    def _complaint_velocity_score(complaint_count_90d: int) -> float:
        """0-10: 2 points per complaint, capped at 10."""
        return float(min(complaint_count_90d * 2, 10))

    @staticmethod
    def _enforcement_history_score(prior_stop_work_orders: int) -> float:
        """0-10: 5 points per SWO, capped at 10."""
        return float(min(prior_stop_work_orders * 5, 10))

    @staticmethod
    def _building_risk_score(building_type: str, stories: int) -> float:
        """0-5: combines building type and height."""
        type_factor = _BUILDING_TYPE_RISK.get(building_type.lower(), 0.5)
        # Height factor: 0 at 1 story, approaches 1 at ~40+ stories
        height_factor = min(stories / _MAX_HEIGHT_STORIES, 1.0)
        return round((type_factor * 3.0) + (height_factor * 2.0), 4)

    @staticmethod
    def _contractor_risk_score(contractor_violation_rate: float) -> float:
        """0-5: violation rate × 5."""
        return min(max(contractor_violation_rate, 0.0), 1.0) * 5.0

    # ------------------------------------------------------------------
    # Fine exposure
    # ------------------------------------------------------------------

    @staticmethod
    def _fine_exposure(violation_classes: list[str], building_type: str) -> float:
        """Estimated USD fine exposure based on violations and building type."""
        total = sum(_FINE_SCHEDULE.get(vc, 0.0) for vc in violation_classes)
        # Commercial buildings attract a 1.5× multiplier in NYC
        if building_type.lower() == "commercial":
            total *= 1.5
        return total

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_project(
        self,
        *,
        violation_classes: list[str] | None = None,
        permit_age_days: int = 0,
        inspection_failures: int = 0,
        inspection_total: int = 0,
        milestone_delay_days: int = 0,
        complaint_count_90d: int = 0,
        prior_stop_work_orders: int = 0,
        building_type: str = "commercial",
        stories: int = 1,
        contractor_violation_rate: float = 0.0,
    ) -> RiskAssessment:
        """Score a project and return a fully populated ``RiskAssessment``."""
        violation_classes = violation_classes or []

        # Component scores
        components: dict[str, float] = {
            "violation_severity_score": self._violation_severity_score(violation_classes),
            "permit_age_score": self._permit_age_score(permit_age_days),
            "inspection_failure_score": self._inspection_failure_score(
                inspection_failures, inspection_total
            ),
            "schedule_delay_score": self._schedule_delay_score(milestone_delay_days),
            "complaint_velocity_score": self._complaint_velocity_score(complaint_count_90d),
            "enforcement_history_score": self._enforcement_history_score(prior_stop_work_orders),
            "building_risk_score": self._building_risk_score(building_type, stories),
            "contractor_risk_score": self._contractor_risk_score(contractor_violation_rate),
        }

        raw_total = sum(components.values())
        risk_score = int(min(max(round(raw_total), 0), 100))

        # Derived probabilities
        stop_work_prob = round(_sigmoid(risk_score, midpoint=65, steepness=0.15), 4)
        insurance_prob = round(_sigmoid(risk_score, midpoint=55, steepness=0.15), 4)

        fine_exposure = self._fine_exposure(violation_classes, building_type)

        # Risk drivers – sorted by contribution, descending
        risk_drivers = [
            name
            for name, _ in sorted(
                components.items(), key=lambda kv: kv[1], reverse=True
            )
            if components[name] > 0
        ]

        features_snapshot: dict[str, Any] = {
            "violation_classes": violation_classes,
            "permit_age_days": permit_age_days,
            "inspection_failures": inspection_failures,
            "inspection_total": inspection_total,
            "milestone_delay_days": milestone_delay_days,
            "complaint_count_90d": complaint_count_90d,
            "prior_stop_work_orders": prior_stop_work_orders,
            "building_type": building_type,
            "stories": stories,
            "contractor_violation_rate": contractor_violation_rate,
        }

        return RiskAssessment(
            risk_score=risk_score,
            stop_work_probability_30d=stop_work_prob,
            insurance_escalation_probability=insurance_prob,
            fine_exposure_estimate=fine_exposure,
            risk_drivers=risk_drivers,
            model_version=self.model_version,
            scored_at=datetime.now(tz=timezone.utc),
            features_snapshot=features_snapshot,
        )

    def explain(self, assessment: RiskAssessment) -> dict:
        """Re-derive all component scores from a ``RiskAssessment``'s snapshot."""
        snap = assessment.features_snapshot
        violation_classes = snap.get("violation_classes", [])

        components: dict[str, float] = {
            "violation_severity_score": self._violation_severity_score(violation_classes),
            "permit_age_score": self._permit_age_score(snap.get("permit_age_days", 0)),
            "inspection_failure_score": self._inspection_failure_score(
                snap.get("inspection_failures", 0),
                snap.get("inspection_total", 0),
            ),
            "schedule_delay_score": self._schedule_delay_score(
                snap.get("milestone_delay_days", 0)
            ),
            "complaint_velocity_score": self._complaint_velocity_score(
                snap.get("complaint_count_90d", 0)
            ),
            "enforcement_history_score": self._enforcement_history_score(
                snap.get("prior_stop_work_orders", 0)
            ),
            "building_risk_score": self._building_risk_score(
                snap.get("building_type", "commercial"),
                snap.get("stories", 1),
            ),
            "contractor_risk_score": self._contractor_risk_score(
                snap.get("contractor_violation_rate", 0.0)
            ),
        }

        return {
            "model_version": assessment.model_version,
            "risk_score": assessment.risk_score,
            "component_scores": components,
            "component_sum": round(sum(components.values()), 4),
            "fine_exposure_estimate": assessment.fine_exposure_estimate,
            "risk_drivers": assessment.risk_drivers,
        }
