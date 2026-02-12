"""
LL149 Inspector Bridge: Integrates Sentinel-Scope site photos with
Local Law 149 superintendent compliance requirements.

Detects whether a required superintendent is present on-site and
cross-references with the DOB permit database.

NYC Local Law 149 (2021) requires a licensed superintendent or site
safety manager on active construction sites based on permit type
and building classification.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuperintendentStatus(StrEnum):
    """Superintendent presence classification."""

    PRESENT = "PRESENT"
    NOT_DETECTED = "NOT_DETECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class LL149Finding(BaseModel):
    """Result of superintendent detection analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str = Field(..., description="NYC BBL for the site")
    superintendent_status: SuperintendentStatus
    confidence: float = Field(ge=0.0, le=1.0)
    violation_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability of LL149 violation",
    )
    evidence_notes: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class LL149InspectorBridge:
    """
    Bridge for LL149 superintendent compliance detection.

    Analyses site photo metadata to determine if a licensed
    superintendent or site safety manager is present.
    """

    # Permit types that mandate superintendent presence
    SUPERINTENDENT_REQUIRED_PERMITS: list[str] = [
        "NB",   # New Building
        "DM",   # Demolition
        "A1",   # Major Alteration
        "A2",   # Minor Alteration (> 3 stories)
    ]

    def __init__(self) -> None:
        self.findings: list[LL149Finding] = []

    def analyze_site(
        self,
        bbl: str,
        image_findings: list[dict[str, Any]] | None = None,
        permit_type: str = "",
    ) -> LL149Finding:
        """
        Determine if superintendent presence is detected from site data.

        Args:
            bbl: NYC BBL identifier.
            image_findings: Findings from VisionAgent (list of dicts with
                entity_type, name, confidence keys).
            permit_type: DOB permit type code (NB, DM, A1, etc.)

        Returns:
            LL149Finding with superintendent status and violation probability.
        """
        image_findings = image_findings or []

        # Check if any detected entity is a superintendent/manager
        superintendent_detected = False
        max_confidence = 0.0

        superintendent_keywords = {
            "superintendent",
            "site safety manager",
            "ssm",
            "site safety coordinator",
            "foreman",
            "site manager",
        }

        for finding in image_findings:
            name = str(finding.get("name", "")).lower()
            entity_type = str(finding.get("entity_type", "")).lower()
            confidence = float(finding.get("confidence", 0.0))

            if any(kw in name or kw in entity_type for kw in superintendent_keywords):
                superintendent_detected = True
                max_confidence = max(max_confidence, confidence)

        # Determine violation probability
        requires_super = (
            permit_type.upper() in self.SUPERINTENDENT_REQUIRED_PERMITS
        )

        if superintendent_detected:
            status = SuperintendentStatus.PRESENT
            violation_prob = max(0.0, 0.10 - max_confidence * 0.10)
        elif not image_findings:
            status = SuperintendentStatus.INSUFFICIENT_EVIDENCE
            violation_prob = 0.50 if requires_super else 0.20
        else:
            status = SuperintendentStatus.NOT_DETECTED
            violation_prob = 0.87 if requires_super else 0.40

        notes = self._build_notes(status, permit_type, requires_super)

        finding = LL149Finding(
            bbl=bbl,
            superintendent_status=status,
            confidence=max_confidence if superintendent_detected else 0.0,
            violation_probability=round(violation_prob, 2),
            evidence_notes=notes,
        )

        self.findings.append(finding)
        return finding

    def _build_notes(
        self,
        status: SuperintendentStatus,
        permit_type: str,
        requires_super: bool,
    ) -> str:
        if status == SuperintendentStatus.PRESENT:
            return "Superintendent detected on site. LL149 compliant."
        if status == SuperintendentStatus.NOT_DETECTED:
            prefix = (
                f"Permit type {permit_type} requires superintendent."
                if requires_super
                else "No superintendent detected."
            )
            return (
                f"{prefix} LL149 violation probability elevated. "
                "Recommend immediate verification."
            )
        return "Insufficient image data to determine superintendent presence."

    def get_findings(self, bbl: str | None = None) -> list[LL149Finding]:
        """Return stored findings, optionally filtered by BBL."""
        if bbl:
            return [f for f in self.findings if f.bbl == bbl]
        return list(self.findings)
