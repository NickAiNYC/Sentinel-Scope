"""
LL152 Gas Tracker Bridge: Integrates Sentinel-Scope site photos with
Local Law 152 gas piping compliance requirements.

Detects visible gas piping installations, flags missing inspection
stickers, and generates GPS-1/GPS-2 form reminders.

NYC Local Law 152 (2016, amended 2019) requires periodic gas piping
inspections for buildings with gas service. Inspections must be
performed by a Licensed Master Plumber (LMP) and results filed
with the DOB.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GasPipingStatus(StrEnum):
    """Gas piping detection classification."""

    COMPLIANT = "COMPLIANT"
    STICKER_MISSING = "STICKER_MISSING"
    PIPING_DETECTED_NO_STICKER = "PIPING_DETECTED_NO_STICKER"
    NO_GAS_PIPING = "NO_GAS_PIPING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class LL152Finding(BaseModel):
    """Result of gas piping compliance analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str = Field(..., description="NYC BBL for the building")
    gas_piping_status: GasPipingStatus
    confidence: float = Field(ge=0.0, le=1.0)
    violation_probability: float = Field(ge=0.0, le=1.0)
    inspection_sticker_detected: bool = False
    gps_form_reminder: str = Field(
        default="",
        description="GPS-1 or GPS-2 form requirement",
    )
    evidence_notes: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class LL152GasTrackerBridge:
    """
    Bridge for LL152 gas piping compliance detection.

    Analyses site photo metadata to identify gas piping
    installations and inspection sticker presence.
    """

    GAS_PIPING_KEYWORDS: list[str] = [
        "gas pipe",
        "gas piping",
        "gas line",
        "gas meter",
        "gas riser",
        "natural gas",
        "gas valve",
        "gas shutoff",
    ]

    STICKER_KEYWORDS: list[str] = [
        "inspection sticker",
        "ll152 sticker",
        "gas inspection",
        "inspection tag",
        "inspection label",
    ]

    def __init__(self) -> None:
        self.findings: list[LL152Finding] = []

    def analyze_site(
        self,
        bbl: str,
        image_findings: list[dict[str, Any]] | None = None,
    ) -> LL152Finding:
        """
        Determine gas piping compliance status from site photo data.

        Args:
            bbl: NYC BBL identifier.
            image_findings: Findings from VisionAgent.

        Returns:
            LL152Finding with gas piping status and violation probability.
        """
        image_findings = image_findings or []

        gas_detected = False
        sticker_detected = False
        max_confidence = 0.0

        for finding in image_findings:
            name = str(finding.get("name", "")).lower()
            notes = str(finding.get("evidence_notes", "")).lower()
            confidence = float(finding.get("confidence", 0.0))
            combined = f"{name} {notes}"

            if any(kw in combined for kw in self.GAS_PIPING_KEYWORDS):
                gas_detected = True
                max_confidence = max(max_confidence, confidence)

            if any(kw in combined for kw in self.STICKER_KEYWORDS):
                sticker_detected = True

        # Classify status
        if not image_findings:
            status = GasPipingStatus.INSUFFICIENT_EVIDENCE
            violation_prob = 0.30
            form_reminder = ""
        elif not gas_detected:
            status = GasPipingStatus.NO_GAS_PIPING
            violation_prob = 0.0
            form_reminder = ""
        elif gas_detected and sticker_detected:
            status = GasPipingStatus.COMPLIANT
            violation_prob = 0.05
            form_reminder = (
                "GPS-2 form on file. Next inspection due per LL152 cycle."
            )
        else:
            status = GasPipingStatus.PIPING_DETECTED_NO_STICKER
            violation_prob = 0.88
            form_reminder = (
                "GPS-1 form required: Schedule inspection with Licensed "
                "Master Plumber. GPS-2 certification form must be filed "
                "with DOB upon completion."
            )

        notes = self._build_notes(status, gas_detected, sticker_detected)

        finding = LL152Finding(
            bbl=bbl,
            gas_piping_status=status,
            confidence=max_confidence if gas_detected else 0.0,
            violation_probability=round(violation_prob, 2),
            inspection_sticker_detected=sticker_detected,
            gps_form_reminder=form_reminder,
            evidence_notes=notes,
        )
        self.findings.append(finding)
        return finding

    def _build_notes(
        self,
        status: GasPipingStatus,
        gas_detected: bool,
        sticker_detected: bool,
    ) -> str:
        if status == GasPipingStatus.COMPLIANT:
            return (
                "Gas piping detected with valid inspection sticker. "
                "LL152 compliant."
            )
        if status == GasPipingStatus.PIPING_DETECTED_NO_STICKER:
            return (
                "Gas piping detected. No inspection sticker found. "
                "LL152 violation imminent. Schedule LMP inspection."
            )
        if status == GasPipingStatus.NO_GAS_PIPING:
            return "No gas piping detected in site imagery."
        return "Insufficient image data for LL152 assessment."

    def get_findings(self, bbl: str | None = None) -> list[LL152Finding]:
        """Return stored findings, optionally filtered by BBL."""
        if bbl:
            return [f for f in self.findings if f.bbl == bbl]
        return list(self.findings)
