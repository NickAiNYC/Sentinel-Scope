"""
OSHA 1926 Construction Safety Violation Detector.

Detects safety violations from construction site imagery:
    - Fall protection (missing guardrails, harnesses) - OSHA 1926.501/502
    - PPE compliance (hard hats, vests, glasses) - OSHA 1926.100/102
    - Scaffolding safety - OSHA 1926.451
    - Excavation protection - OSHA 1926.651
    - Electrical safety - OSHA 1926.405
    - Ladder safety - OSHA 1926.1053
    - Housekeeping - OSHA 1926.25
    - Fire protection - OSHA 1926.150
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ViolationType(StrEnum):
    """OSHA 1926 violation categories."""

    FALL_PROTECTION = "FALL_PROTECTION"
    PPE_NONCOMPLIANCE = "PPE_NONCOMPLIANCE"
    SCAFFOLDING = "SCAFFOLDING"
    EXCAVATION = "EXCAVATION"
    ELECTRICAL = "ELECTRICAL"
    LADDER = "LADDER"
    HOUSEKEEPING = "HOUSEKEEPING"
    FIRE_PROTECTION = "FIRE_PROTECTION"


class SeverityLevel(StrEnum):
    """OSHA violation severity classification."""

    IMMINENT_DANGER = "IMMINENT_DANGER"
    SERIOUS = "SERIOUS"
    OTHER_THAN_SERIOUS = "OTHER_THAN_SERIOUS"
    WILLFUL = "WILLFUL"


class SafetyViolation(BaseModel):
    """A single detected safety violation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    violation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    violation_type: ViolationType
    osha_standard: str = Field(
        ..., description="OSHA standard reference (e.g. 1926.501)"
    )
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    recommended_action: str
    stop_work_required: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


class SafetyAnalysisResult(BaseModel):
    """Aggregated safety analysis for a site."""

    model_config = ConfigDict(str_strip_whitespace=True)

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str
    violations: list[SafetyViolation] = Field(default_factory=list)
    total_violations: int = 0
    stop_work_violations: int = 0
    overall_risk: str = "LOW"
    timestamp: datetime = Field(default_factory=datetime.now)


# Keyword-to-violation mapping
_VIOLATION_RULES: list[dict[str, Any]] = [
    {
        "type": ViolationType.FALL_PROTECTION,
        "osha": "1926.501",
        "severity": SeverityLevel.IMMINENT_DANGER,
        "keywords": [
            "no fall protection", "missing guardrail", "no guardrail",
            "no harness", "missing harness", "unprotected edge",
            "no safety net", "fall hazard",
        ],
        "action": "Install guardrails or personal fall arrest systems immediately.",
        "stop_work": True,
    },
    {
        "type": ViolationType.PPE_NONCOMPLIANCE,
        "osha": "1926.100",
        "severity": SeverityLevel.SERIOUS,
        "keywords": [
            "no hard hat", "missing hard hat", "no helmet",
            "no safety vest", "no safety glasses", "no ppe",
            "missing ppe", "no eye protection",
        ],
        "action": "Distribute required PPE and enforce usage on site.",
        "stop_work": False,
    },
    {
        "type": ViolationType.SCAFFOLDING,
        "osha": "1926.451",
        "severity": SeverityLevel.SERIOUS,
        "keywords": [
            "unsafe scaffold", "scaffolding violation",
            "missing scaffold plank", "no toe board",
            "scaffold overloaded", "damaged scaffold",
        ],
        "action": "Remove workers from scaffold. Inspect and repair before reuse.",
        "stop_work": True,
    },
    {
        "type": ViolationType.EXCAVATION,
        "osha": "1926.651",
        "severity": SeverityLevel.IMMINENT_DANGER,
        "keywords": [
            "unshored excavation", "no trench box",
            "cave-in hazard", "no shoring", "trench collapse",
            "excavation unprotected",
        ],
        "action": "Install shoring or trench boxes. No entry until protected.",
        "stop_work": True,
    },
    {
        "type": ViolationType.ELECTRICAL,
        "osha": "1926.405",
        "severity": SeverityLevel.SERIOUS,
        "keywords": [
            "exposed wiring", "electrical hazard",
            "no gfci", "damaged cord", "live wire",
        ],
        "action": "De-energize circuit. Repair or replace damaged equipment.",
        "stop_work": True,
    },
    {
        "type": ViolationType.LADDER,
        "osha": "1926.1053",
        "severity": SeverityLevel.OTHER_THAN_SERIOUS,
        "keywords": [
            "damaged ladder", "ladder violation",
            "ladder not secured", "improper ladder",
        ],
        "action": "Remove damaged ladder from service. Provide compliant replacement.",
        "stop_work": False,
    },
    {
        "type": ViolationType.HOUSEKEEPING,
        "osha": "1926.25",
        "severity": SeverityLevel.OTHER_THAN_SERIOUS,
        "keywords": [
            "debris", "cluttered", "housekeeping violation",
            "tripping hazard", "blocked exit",
        ],
        "action": "Clear debris and restore safe access paths.",
        "stop_work": False,
    },
    {
        "type": ViolationType.FIRE_PROTECTION,
        "osha": "1926.150",
        "severity": SeverityLevel.SERIOUS,
        "keywords": [
            "no fire extinguisher", "missing fire extinguisher",
            "blocked fire exit", "no fire watch",
            "hot work no permit",
        ],
        "action": "Provide fire extinguishers and establish fire watch as required.",
        "stop_work": False,
    },
]


class SafetyViolationDetector:
    """
    Detects OSHA 1926 safety violations from construction site
    image analysis findings.
    """

    def __init__(self) -> None:
        self.results: list[SafetyAnalysisResult] = []

    def analyze(
        self,
        bbl: str,
        image_findings: list[dict[str, Any]] | None = None,
    ) -> SafetyAnalysisResult:
        """
        Scan image findings for OSHA violations.

        Args:
            bbl: NYC BBL identifier.
            image_findings: List of dicts with name/evidence_notes/confidence keys.

        Returns:
            SafetyAnalysisResult with detected violations.
        """
        image_findings = image_findings or []
        violations: list[SafetyViolation] = []
        seen_types: set[ViolationType] = set()

        for finding in image_findings:
            name = str(finding.get("name", "")).lower()
            notes = str(finding.get("evidence_notes", "")).lower()
            confidence = float(finding.get("confidence", 0.0))
            combined = f"{name} {notes}"

            for rule in _VIOLATION_RULES:
                vtype: ViolationType = rule["type"]
                if vtype in seen_types:
                    continue
                if any(kw in combined for kw in rule["keywords"]):
                    violations.append(
                        SafetyViolation(
                            violation_type=vtype,
                            osha_standard=rule["osha"],
                            severity=rule["severity"],
                            confidence=confidence,
                            description=(
                                f"{vtype.value} detected: {name or notes[:80]}"
                            ),
                            recommended_action=rule["action"],
                            stop_work_required=rule["stop_work"],
                        )
                    )
                    seen_types.add(vtype)

        stop_work_count = sum(1 for v in violations if v.stop_work_required)
        if stop_work_count > 0:
            risk = "CRITICAL"
        elif len(violations) >= 3:
            risk = "HIGH"
        elif violations:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        result = SafetyAnalysisResult(
            bbl=bbl,
            violations=violations,
            total_violations=len(violations),
            stop_work_violations=stop_work_count,
            overall_risk=risk,
        )
        self.results.append(result)
        return result

    def get_results(self, bbl: str | None = None) -> list[SafetyAnalysisResult]:
        """Return stored results, optionally filtered by BBL."""
        if bbl:
            return [r for r in self.results if r.bbl == bbl]
        return list(self.results)
