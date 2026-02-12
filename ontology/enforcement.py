"""Enforcement categories and escalation graph for compliance workflows."""

from __future__ import annotations

from enum import StrEnum


class EnforcementCategory(StrEnum):
    """Types of enforcement actions available to a regulatory authority."""

    ADMINISTRATIVE = "administrative"
    CIVIL_PENALTY = "civil_penalty"
    STOP_WORK_ORDER = "stop_work_order"
    VACATE_ORDER = "vacate_order"
    CRIMINAL_REFERRAL = "criminal_referral"


class EscalationLevel(StrEnum):
    """Graduated escalation levels ordered by severity."""

    NOTICE = "notice"
    WARNING = "warning"
    CITATION = "citation"
    ORDER = "order"
    EMERGENCY = "emergency"


class EscalationGraph:
    """Maps risk scores to escalation levels and likely enforcement actions.

    The thresholds and mappings are jurisdiction-agnostic defaults that can
    be overridden per deployment.
    """

    _SCORE_BANDS: list[tuple[int, int, EscalationLevel]] = [
        (0, 20, EscalationLevel.NOTICE),
        (21, 40, EscalationLevel.WARNING),
        (41, 60, EscalationLevel.CITATION),
        (61, 80, EscalationLevel.ORDER),
        (81, 100, EscalationLevel.EMERGENCY),
    ]

    _ENFORCEMENT_MAP: dict[EscalationLevel, dict[str, list[EnforcementCategory]]] = {
        EscalationLevel.NOTICE: {
            "default": [EnforcementCategory.ADMINISTRATIVE],
        },
        EscalationLevel.WARNING: {
            "default": [EnforcementCategory.ADMINISTRATIVE, EnforcementCategory.CIVIL_PENALTY],
        },
        EscalationLevel.CITATION: {
            "default": [EnforcementCategory.CIVIL_PENALTY],
            "hazardous": [EnforcementCategory.CIVIL_PENALTY, EnforcementCategory.STOP_WORK_ORDER],
        },
        EscalationLevel.ORDER: {
            "default": [EnforcementCategory.STOP_WORK_ORDER, EnforcementCategory.CIVIL_PENALTY],
            "hazardous": [
                EnforcementCategory.STOP_WORK_ORDER,
                EnforcementCategory.VACATE_ORDER,
                EnforcementCategory.CIVIL_PENALTY,
            ],
        },
        EscalationLevel.EMERGENCY: {
            "default": [
                EnforcementCategory.STOP_WORK_ORDER,
                EnforcementCategory.VACATE_ORDER,
            ],
            "hazardous": [
                EnforcementCategory.STOP_WORK_ORDER,
                EnforcementCategory.VACATE_ORDER,
                EnforcementCategory.CRIMINAL_REFERRAL,
            ],
        },
    }

    @classmethod
    def get_escalation_level(cls, risk_score: int) -> EscalationLevel:
        """Return the escalation level for a given *risk_score* (0-100)."""
        for low, high, level in cls._SCORE_BANDS:
            if low <= risk_score <= high:
                return level
        # Clamp out-of-range scores to the nearest boundary.
        if risk_score < 0:
            return EscalationLevel.NOTICE
        return EscalationLevel.EMERGENCY

    @classmethod
    def get_likely_enforcement(
        cls,
        risk_score: int,
        violation_class: str,
    ) -> list[EnforcementCategory]:
        """Return probable enforcement categories for a risk score and class.

        *violation_class* is a free-form string.  If it contains the
        substring ``"hazardous"`` (case-insensitive), the hazardous
        enforcement track is used when available.
        """
        level = cls.get_escalation_level(risk_score)
        level_map = cls._ENFORCEMENT_MAP.get(level, {})
        key = "hazardous" if "hazardous" in violation_class.lower() else "default"
        return list(level_map.get(key, level_map.get("default", [])))
