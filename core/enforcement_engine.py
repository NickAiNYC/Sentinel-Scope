"""Enforcement forecasting engine for construction compliance workflows."""

from __future__ import annotations

import math

from ontology.enforcement import EscalationGraph, EscalationLevel


def _sigmoid(x: float, midpoint: float, steepness: float = 0.15) -> float:
    """Standard sigmoid mapped to [0, 1]."""
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


_RECOMMENDED_ACTIONS: dict[EscalationLevel, list[str]] = {
    EscalationLevel.NOTICE: [
        "Review and acknowledge notice within 10 business days",
        "Document current compliance status",
    ],
    EscalationLevel.WARNING: [
        "Submit corrective action plan within 15 days",
        "Schedule voluntary re-inspection",
        "Assign dedicated compliance officer to project",
    ],
    EscalationLevel.CITATION: [
        "Engage licensed expediter to resolve open violations",
        "File cure plan with DOB within 10 days",
        "Halt non-essential work in affected areas until citation is addressed",
    ],
    EscalationLevel.ORDER: [
        "Immediately address all Class C violations",
        "Retain compliance counsel for DOB hearing preparation",
        "Submit stop-work order response plan within 5 days",
        "Notify insurance carrier of pending enforcement action",
    ],
    EscalationLevel.EMERGENCY: [
        "Cease all construction activity immediately",
        "Secure the site and ensure public safety measures are in place",
        "Engage emergency compliance counsel",
        "Coordinate with DOB for emergency inspection",
        "Notify insurance carrier and bonding company immediately",
    ],
}


class EnforcementEngine:
    """Forecasts likely enforcement actions and stop-work probability."""

    def forecast_enforcement(
        self,
        risk_score: int,
        violation_classes: list[str],
        prior_stop_work_orders: int = 0,
        permit_age_days: int = 0,
    ) -> dict:
        """Produce an enforcement forecast for a project.

        Parameters
        ----------
        risk_score:
            Composite risk score (0-100).
        violation_classes:
            List of violation class strings (e.g. ``["Class A", "Class C"]``).
        prior_stop_work_orders:
            Number of prior stop-work orders on file.
        permit_age_days:
            Age of the primary permit in days.

        Returns
        -------
        dict
            Enforcement forecast containing escalation level, likely actions,
            stop-work probabilities, recommended actions, and timeline.
        """
        escalation_level = EscalationGraph.get_escalation_level(risk_score)

        # Aggregate likely enforcement actions across all violation classes
        seen: set[str] = set()
        likely_actions: list[str] = []
        classes = violation_classes if violation_classes else [""]
        for vc in classes:
            for action in EscalationGraph.get_likely_enforcement(risk_score, vc):
                action_str = str(action)
                if action_str not in seen:
                    seen.add(action_str)
                    likely_actions.append(action_str)

        # --- Stop-work probability (30-day) ---
        has_class_c = any(vc == "Class C" for vc in violation_classes)

        # Base probability from risk score via sigmoid (midpoint 65)
        base_prob = _sigmoid(risk_score, midpoint=65, steepness=0.15)

        # Boost for Class C violations
        if has_class_c:
            base_prob += 0.15

        # Boost for prior stop-work orders (diminishing returns)
        if prior_stop_work_orders > 0:
            base_prob += min(prior_stop_work_orders * 0.10, 0.25)

        # Permit age factor: older permits slightly increase risk
        if permit_age_days > 365:
            base_prob += min((permit_age_days - 365) / 3650, 0.10)

        stop_work_30d = round(min(base_prob, 1.0), 4)
        stop_work_60d = round(min(stop_work_30d * 1.3, 1.0), 4)

        # --- Timeline estimation ---
        if risk_score >= 80:
            timeline_days = 7
        elif risk_score >= 60:
            timeline_days = 30
        else:
            timeline_days = 90

        # --- Recommended actions ---
        recommended = list(
            _RECOMMENDED_ACTIONS.get(escalation_level, [])
        )

        return {
            "escalation_level": str(escalation_level),
            "likely_enforcement_actions": likely_actions,
            "stop_work_probability_30d": stop_work_30d,
            "stop_work_probability_60d": stop_work_60d,
            "recommended_actions": recommended,
            "timeline_days": timeline_days,
        }
