"""
Progress Tracker AI: Automated construction milestone verification.

Tracks:
    - Schedule vs. actual percent complete
    - Milestone achievement based on image evidence
    - Change order evidence collection
    - Lien waiver milestone tracking
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.constants import MILESTONES


class MilestoneStatus(BaseModel):
    """Status of a single construction milestone."""

    model_config = ConfigDict(str_strip_whitespace=True)

    milestone_key: str
    milestone_name: str
    scheduled_pct: float = Field(ge=0.0, le=100.0, default=0.0)
    actual_pct: float = Field(ge=0.0, le=100.0, default=0.0)
    variance: float = Field(
        default=0.0,
        description="actual_pct - scheduled_pct (negative = behind)",
    )
    evidence_count: int = Field(default=0, ge=0)
    verified: bool = False


class ProgressReport(BaseModel):
    """Aggregated progress report for a construction site."""

    model_config = ConfigDict(str_strip_whitespace=True)

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str
    milestones: list[MilestoneStatus] = Field(default_factory=list)
    overall_pct_complete: float = Field(ge=0.0, le=100.0, default=0.0)
    schedule_variance_weeks: float = Field(
        default=0.0,
        description="Positive = ahead, negative = behind schedule",
    )
    change_orders: list[dict[str, Any]] = Field(default_factory=list)
    lien_waiver_milestones: list[str] = Field(default_factory=list)
    summary: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)


class ProgressTrackerAI:
    """
    Automated construction progress tracking using image-based
    milestone verification.
    """

    def __init__(self) -> None:
        self.reports: list[ProgressReport] = []

    def analyze_progress(
        self,
        bbl: str,
        image_findings: list[dict[str, Any]] | None = None,
        scheduled: dict[str, float] | None = None,
        change_orders: list[dict[str, Any]] | None = None,
    ) -> ProgressReport:
        """
        Compute progress for each milestone based on image evidence.

        Args:
            bbl: NYC BBL identifier.
            image_findings: VisionAgent findings with milestone/confidence keys.
            scheduled: Expected percent-complete per milestone key
                       (e.g. {"EXCAVATION": 100.0, "SUPERSTRUCTURE": 50.0}).
            change_orders: List of change order records.

        Returns:
            ProgressReport with milestone statuses and overall progress.
        """
        image_findings = image_findings or []
        scheduled = scheduled or {}
        change_orders = change_orders or []

        # Count evidence per milestone
        evidence_map: dict[str, list[float]] = {}
        for finding in image_findings:
            milestone_raw = str(finding.get("milestone", "")).upper().replace(" ", "_")
            confidence = float(finding.get("confidence", 0.0))
            if not milestone_raw:
                continue
            # Match against known milestone keys
            for key in MILESTONES:
                if key in milestone_raw or milestone_raw in key:
                    evidence_map.setdefault(key, []).append(confidence)
                    break

        # Build milestone statuses
        milestone_statuses: list[MilestoneStatus] = []
        for key, name in MILESTONES.items():
            evidences = evidence_map.get(key, [])
            actual_pct = 0.0
            if evidences:
                avg_conf = sum(evidences) / len(evidences)
                actual_pct = round(min(100.0, avg_conf * 100), 1)

            sched_pct = scheduled.get(key, 0.0)
            variance = round(actual_pct - sched_pct, 1)

            milestone_statuses.append(
                MilestoneStatus(
                    milestone_key=key,
                    milestone_name=name,
                    scheduled_pct=sched_pct,
                    actual_pct=actual_pct,
                    variance=variance,
                    evidence_count=len(evidences),
                    verified=len(evidences) > 0 and actual_pct >= 95.0,
                )
            )

        # Overall progress: average of actual percentages
        if milestone_statuses:
            overall = round(
                sum(m.actual_pct for m in milestone_statuses)
                / len(milestone_statuses),
                1,
            )
        else:
            overall = 0.0

        # Schedule variance in weeks (rough: 1% ≈ 0.2 weeks for typical project)
        avg_variance = 0.0
        active = [m for m in milestone_statuses if m.scheduled_pct > 0]
        if active:
            avg_variance = (
                sum(m.variance for m in active) / len(active)
            )
        schedule_weeks = round(avg_variance * 0.2, 1)

        # Lien waiver milestones: milestones that are 100% complete
        lien_milestones = [
            m.milestone_name
            for m in milestone_statuses
            if m.actual_pct >= 100.0
        ]

        summary = self._build_summary(milestone_statuses, overall, schedule_weeks)

        report = ProgressReport(
            bbl=bbl,
            milestones=milestone_statuses,
            overall_pct_complete=overall,
            schedule_variance_weeks=schedule_weeks,
            change_orders=change_orders,
            lien_waiver_milestones=lien_milestones,
            summary=summary,
        )
        self.reports.append(report)
        return report

    def _build_summary(
        self,
        milestones: list[MilestoneStatus],
        overall: float,
        schedule_weeks: float,
    ) -> str:
        parts: list[str] = []
        for m in milestones:
            if m.actual_pct > 0:
                parts.append(f"{m.milestone_name} {m.actual_pct}% complete.")

        schedule_note = (
            f"{abs(schedule_weeks)} weeks behind schedule."
            if schedule_weeks < 0
            else f"{schedule_weeks} weeks ahead of schedule."
            if schedule_weeks > 0
            else "On schedule."
        )
        parts.append(schedule_note)
        parts.insert(0, f"Overall: {overall}% complete.")
        return " ".join(parts)

    def get_reports(self, bbl: str | None = None) -> list[ProgressReport]:
        """Return stored reports, optionally filtered by BBL."""
        if bbl:
            return [r for r in self.reports if r.bbl == bbl]
        return list(self.reports)
