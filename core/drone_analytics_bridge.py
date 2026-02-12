"""
Drone Analytics Bridge: Aerial site intelligence for construction monitoring.

Capabilities:
    - Drone footage metadata ingestion and analysis
    - Volume calculations (excavation, concrete pours)
    - Site progress estimation from aerial coverage
    - 4D timeline data structure for visualization
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DroneCapture(BaseModel):
    """Metadata for a single drone capture/flight."""

    model_config = ConfigDict(str_strip_whitespace=True)

    capture_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str
    flight_date: datetime = Field(default_factory=datetime.now)
    area_acres: float = Field(ge=0.0, default=0.0)
    altitude_ft: float = Field(ge=0.0, default=0.0)
    image_count: int = Field(ge=0, default=0)
    gps_coordinates: list[tuple[float, float]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VolumeEstimate(BaseModel):
    """Volume calculation from drone survey data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    material: str = Field(
        ..., description="e.g., excavation, concrete, fill"
    )
    volume_cy: float = Field(
        ge=0.0, description="Volume in cubic yards"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.85)


class TimelineEntry(BaseModel):
    """A single entry in the 4D construction timeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    milestone: str
    progress_pct: float = Field(ge=0.0, le=100.0)
    capture_id: str | None = None
    notes: str = ""


class DroneAnalysisResult(BaseModel):
    """Aggregated result from drone analytics."""

    model_config = ConfigDict(str_strip_whitespace=True)

    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bbl: str
    captures: list[DroneCapture] = Field(default_factory=list)
    total_area_acres: float = Field(ge=0.0, default=0.0)
    total_images: int = Field(ge=0, default=0)
    volumes: list[VolumeEstimate] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    site_progress_pct: float = Field(ge=0.0, le=100.0, default=0.0)
    processing_time_sec: float = Field(ge=0.0, default=0.0)
    summary: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class DroneAnalyticsBridge:
    """
    Bridge for drone footage analysis and site intelligence.
    """

    # Target: < 5 min per acre (300 seconds)
    MAX_PROCESSING_SEC_PER_ACRE = 300.0

    def __init__(self) -> None:
        self.results: list[DroneAnalysisResult] = []

    def ingest_captures(
        self,
        bbl: str,
        captures: list[dict[str, Any]] | None = None,
    ) -> list[DroneCapture]:
        """
        Ingest drone flight metadata.

        Args:
            bbl: NYC BBL identifier.
            captures: List of capture dicts with area_acres, altitude_ft,
                image_count, gps_coordinates, flight_date keys.

        Returns:
            List of DroneCapture objects.
        """
        captures = captures or []
        result: list[DroneCapture] = []

        for raw in captures:
            capture = DroneCapture(
                bbl=bbl,
                area_acres=float(raw.get("area_acres", 0.0)),
                altitude_ft=float(raw.get("altitude_ft", 0.0)),
                image_count=int(raw.get("image_count", 0)),
                gps_coordinates=raw.get("gps_coordinates", []),
                metadata=raw.get("metadata", {}),
            )
            if "flight_date" in raw:
                capture.flight_date = datetime.fromisoformat(
                    str(raw["flight_date"])
                )
            result.append(capture)

        return result

    def estimate_volumes(
        self,
        image_findings: list[dict[str, Any]] | None = None,
    ) -> list[VolumeEstimate]:
        """
        Estimate material volumes from image analysis findings.

        Uses detection keywords and reported measurements.
        """
        image_findings = image_findings or []
        volumes: list[VolumeEstimate] = []
        seen: set[str] = set()

        material_keywords: dict[str, list[str]] = {
            "excavation": ["excavation", "excavated", "trench", "dig"],
            "concrete": ["concrete", "pour", "slab", "footing"],
            "fill": ["fill", "backfill", "grading"],
        }

        for finding in image_findings:
            name = str(finding.get("name", "")).lower()
            notes = str(finding.get("evidence_notes", "")).lower()
            combined = f"{name} {notes}"
            volume_cy = float(finding.get("volume_cy", 0.0))
            confidence = float(finding.get("confidence", 0.85))

            for material, kws in material_keywords.items():
                if material in seen:
                    continue
                if any(kw in combined for kw in kws):
                    volumes.append(
                        VolumeEstimate(
                            material=material,
                            volume_cy=volume_cy,
                            confidence=confidence,
                        )
                    )
                    seen.add(material)

        return volumes

    def analyze(
        self,
        bbl: str,
        captures: list[dict[str, Any]] | None = None,
        image_findings: list[dict[str, Any]] | None = None,
        timeline_entries: list[dict[str, Any]] | None = None,
    ) -> DroneAnalysisResult:
        """
        Run full drone analytics pipeline.

        Args:
            bbl: NYC BBL identifier.
            captures: Raw capture metadata dicts.
            image_findings: VisionAgent findings with volume/material data.
            timeline_entries: Manual or auto-generated timeline entries.

        Returns:
            DroneAnalysisResult with volumes, timeline, and progress.
        """
        drone_captures = self.ingest_captures(bbl, captures)
        volumes = self.estimate_volumes(image_findings)

        # Timeline
        timeline: list[TimelineEntry] = []
        for entry in (timeline_entries or []):
            timeline.append(
                TimelineEntry(
                    date=datetime.fromisoformat(
                        str(entry.get("date", datetime.now().isoformat()))
                    ),
                    milestone=str(entry.get("milestone", "")),
                    progress_pct=float(entry.get("progress_pct", 0.0)),
                    capture_id=entry.get("capture_id"),
                    notes=str(entry.get("notes", "")),
                )
            )

        total_area = sum(c.area_acres for c in drone_captures)
        total_images = sum(c.image_count for c in drone_captures)

        # Estimated processing time (simulated)
        processing_time = total_area * self.MAX_PROCESSING_SEC_PER_ACRE * 0.5

        # Progress from timeline
        progress = 0.0
        if timeline:
            progress = max(e.progress_pct for e in timeline)

        summary = (
            f"Drone survey complete: {total_images} images over "
            f"{total_area:.1f} acres. "
        )
        if volumes:
            vol_parts = [
                f"{v.volume_cy:,.0f} CY {v.material}" for v in volumes
            ]
            summary += " | ".join(vol_parts) + ". "
        summary += f"{progress:.0f}% of planned progress."

        result = DroneAnalysisResult(
            bbl=bbl,
            captures=drone_captures,
            total_area_acres=total_area,
            total_images=total_images,
            volumes=volumes,
            timeline=timeline,
            site_progress_pct=progress,
            processing_time_sec=processing_time,
            summary=summary,
        )
        self.results.append(result)
        return result

    def get_results(self, bbl: str | None = None) -> list[DroneAnalysisResult]:
        """Return stored results, optionally filtered by BBL."""
        if bbl:
            return [r for r in self.results if r.bbl == bbl]
        return list(self.results)
