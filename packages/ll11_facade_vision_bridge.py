"""
LL11 Facade Vision Bridge: Integrates Sentinel-Scope facade photos with
Local Law 11 (FISP) compliance requirements.

Detects unsafe facade conditions (cracks, spalling, bulges) from site
imagery. Applies a pre-1950 risk multiplier and auto-flags for
Critical Examination Report when warranted.

NYC Local Law 11 / Facade Inspection & Safety Program (FISP) requires
periodic facade inspections of buildings greater than 6 stories.
Cycle 9 began February 2020.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FacadeCondition(StrEnum):
    """Facade condition classification per FISP categories."""

    SAFE = "SAFE"
    # SWARMP: Safe With A Repair & Maintenance Program (FISP term)
    SAFE_WITH_REPAIR = "SWARMP"
    UNSAFE = "UNSAFE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class LL11Finding(BaseModel):
    """Result of facade condition analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str = Field(..., description="NYC BBL for the building")
    facade_condition: FacadeCondition
    confidence: float = Field(ge=0.0, le=1.0)
    violation_probability: float = Field(ge=0.0, le=1.0)
    defects_detected: list[str] = Field(default_factory=list)
    pre_1950_multiplier: float = Field(
        default=1.0,
        description="Risk multiplier for pre-1950 buildings (2.8x)",
    )
    critical_exam_required: bool = Field(
        default=False,
        description="Whether a Critical Examination Report is recommended",
    )
    evidence_notes: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class LL11FacadeVisionBridge:
    """
    Bridge for LL11/FISP facade compliance detection.

    Analyses facade imagery for cracks, spalling, bulges, and other
    unsafe conditions. Buildings constructed before 1950 receive an
    elevated risk multiplier of 2.8x.
    """

    PRE_1950_MULTIPLIER = 2.8

    DEFECT_KEYWORDS: dict[str, list[str]] = {
        "crack": ["crack", "fracture", "fissure", "split"],
        "spalling": ["spalling", "spall", "flaking", "delamination"],
        "bulge": ["bulge", "bulging", "bow", "bowing", "buckle"],
        "corrosion": ["corrosion", "rust", "oxidation", "rusting"],
        "missing_material": [
            "missing", "hole", "void", "gap", "fallen",
            "loose", "detached",
        ],
        "water_damage": ["water damage", "efflorescence", "staining", "leak"],
    }

    def __init__(self) -> None:
        self.findings: list[LL11Finding] = []

    def analyze_facade(
        self,
        bbl: str,
        image_findings: list[dict[str, Any]] | None = None,
        year_built: int | None = None,
        stories: int | None = None,
    ) -> LL11Finding:
        """
        Assess facade condition from site photo data.

        Args:
            bbl: NYC BBL identifier.
            image_findings: Findings from VisionAgent containing
                name/evidence_notes/confidence keys.
            year_built: Year the building was constructed.
            stories: Number of stories (LL11 applies to > 6).

        Returns:
            LL11Finding with facade condition and violation probability.
        """
        image_findings = image_findings or []

        defects: list[str] = []
        max_confidence = 0.0

        for finding in image_findings:
            name = str(finding.get("name", "")).lower()
            notes = str(finding.get("evidence_notes", "")).lower()
            confidence = float(finding.get("confidence", 0.0))
            combined = f"{name} {notes}"

            for defect_type, keywords in self.DEFECT_KEYWORDS.items():
                if any(kw in combined for kw in keywords):
                    if defect_type not in defects:
                        defects.append(defect_type)
                    max_confidence = max(max_confidence, confidence)

        # Pre-1950 multiplier
        is_pre_1950 = year_built is not None and year_built < 1950
        multiplier = self.PRE_1950_MULTIPLIER if is_pre_1950 else 1.0

        # Determine condition
        if not image_findings:
            condition = FacadeCondition.INSUFFICIENT_EVIDENCE
            base_prob = 0.30
            critical_exam = False
        elif not defects:
            condition = FacadeCondition.SAFE
            base_prob = 0.05
            critical_exam = False
        elif len(defects) >= 3 or "crack" in defects:
            condition = FacadeCondition.UNSAFE
            base_prob = 0.85
            critical_exam = True
        else:
            condition = FacadeCondition.SAFE_WITH_REPAIR
            base_prob = 0.45
            critical_exam = False

        violation_prob = min(1.0, base_prob * multiplier)

        notes = self._build_notes(
            condition, defects, is_pre_1950, critical_exam, stories
        )

        finding = LL11Finding(
            bbl=bbl,
            facade_condition=condition,
            confidence=max_confidence if defects else 0.0,
            violation_probability=round(violation_prob, 2),
            defects_detected=defects,
            pre_1950_multiplier=multiplier,
            critical_exam_required=critical_exam,
            evidence_notes=notes,
        )
        self.findings.append(finding)
        return finding

    def _build_notes(
        self,
        condition: FacadeCondition,
        defects: list[str],
        is_pre_1950: bool,
        critical_exam: bool,
        stories: int | None,
    ) -> str:
        parts: list[str] = []

        if condition == FacadeCondition.UNSAFE:
            parts.append(
                f"Facade defects detected: {', '.join(defects)}. "
                "Condition classified as UNSAFE per FISP."
            )
        elif condition == FacadeCondition.SAFE_WITH_REPAIR:
            parts.append(
                f"Facade defects detected: {', '.join(defects)}. "
                "Condition: Safe With A Repair & Maintenance Program (SWARMP)."
            )
        elif condition == FacadeCondition.SAFE:
            parts.append("No facade defects detected. Condition: SAFE.")
        else:
            parts.append("Insufficient image data for facade assessment.")

        if is_pre_1950:
            parts.append(
                "Pre-1950 building: risk multiplier "
                f"{self.PRE_1950_MULTIPLIER}x applied."
            )

        if critical_exam:
            parts.append(
                "Critical Examination Report recommended. "
                "File with DOB within 30 days per LL11/FISP."
            )

        if stories is not None and stories <= 6:
            parts.append(
                f"Building has {stories} stories. LL11/FISP applies to "
                "buildings > 6 stories only."
            )

        return " ".join(parts)

    def get_findings(self, bbl: str | None = None) -> list[LL11Finding]:
        """Return stored findings, optionally filtered by BBL."""
        if bbl:
            return [f for f in self.findings if f.bbl == bbl]
        return list(self.findings)
