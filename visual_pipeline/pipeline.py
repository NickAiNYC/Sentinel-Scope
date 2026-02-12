"""Visual forensics pipeline for construction site image analysis."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from workers.task_queue import TaskQueue


class ImageJob(BaseModel):
    """A submitted image analysis job."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    image_source: str
    tenant_id: str = "default"
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    status: str = "pending"


class ImageJobResult(BaseModel):
    """Result of processing an image job."""

    job_id: str
    project_id: str
    milestones_detected: list[str] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    ocr_text: str | None = None
    metadata_extracted: dict = Field(default_factory=dict)
    duplicate_hash: str | None = None
    permit_correlation_id: str | None = None
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class VisualForensicsPipeline:
    """Orchestrates image ingestion, analysis, and deduplication."""

    def __init__(self, task_queue: TaskQueue | None = None) -> None:
        self._task_queue = task_queue
        self._jobs: dict[str, ImageJob] = {}
        self._results: dict[str, ImageJobResult] = {}

        if self._task_queue is not None:
            self._task_queue.register("image_analysis", self._handle_task)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_image(
        self,
        project_id: str,
        image_source: str,
        tenant_id: str = "default",
    ) -> ImageJob:
        """Create and queue an image analysis job."""
        job = ImageJob(
            project_id=project_id,
            image_source=image_source,
            tenant_id=tenant_id,
        )
        self._jobs[job.job_id] = job

        if self._task_queue is not None:
            self._task_queue.submit(
                task_name="image_analysis",
                payload={"job_id": job.job_id},
                tenant_id=tenant_id,
            )

        return job

    def get_job_status(self, job_id: str) -> dict:
        """Return status information for a job."""
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job {job_id} not found")
        return {
            "job_id": job.job_id,
            "status": job.status,
            "project_id": job.project_id,
            "submitted_at": job.submitted_at.isoformat(),
        }

    def get_project_jobs(self, project_id: str) -> list[ImageJob]:
        """Return all jobs associated with a project."""
        return [j for j in self._jobs.values() if j.project_id == project_id]

    def process_image(self, job_id: str) -> ImageJobResult:
        """Process an image job (mock implementation).

        Generates milestone detections, computes a SHA-256 hash of the
        image source for deduplication, and returns an ``ImageJobResult``.
        """
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job {job_id} not found")

        job.status = "processing"

        image_hash = self._compute_hash(job.image_source)

        milestones = self._detect_milestones(job.image_source)
        confidence = {m: round(0.85 + 0.1 * (i % 2), 2) for i, m in enumerate(milestones)}

        result = ImageJobResult(
            job_id=job.job_id,
            project_id=job.project_id,
            milestones_detected=milestones,
            confidence_scores=confidence,
            ocr_text=f"Mock OCR for {job.image_source}",
            metadata_extracted={"source": job.image_source, "tenant_id": job.tenant_id},
            duplicate_hash=image_hash,
        )

        self._results[job.job_id] = result
        job.status = "completed"
        return result

    def detect_duplicates(self, project_id: str) -> list[tuple[str, str]]:
        """Find pairs of jobs that share the same image hash within a project."""
        project_results = [
            r for r in self._results.values() if r.project_id == project_id
        ]

        hash_to_jobs: dict[str, list[str]] = {}
        for r in project_results:
            if r.duplicate_hash is not None:
                hash_to_jobs.setdefault(r.duplicate_hash, []).append(r.job_id)

        duplicates: list[tuple[str, str]] = []
        for job_ids in hash_to_jobs.values():
            for i in range(len(job_ids)):
                for j in range(i + 1, len(job_ids)):
                    duplicates.append((job_ids[i], job_ids[j]))
        return duplicates

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_task(self, payload: dict) -> dict:
        """TaskQueue handler for ``image_analysis`` tasks."""
        result = self.process_image(payload["job_id"])
        return result.model_dump()

    @staticmethod
    def _compute_hash(image_source: str) -> str:
        """Return SHA-256 hex digest for an image source.

        If *image_source* points to an existing file the file bytes are
        hashed; otherwise the source string itself is hashed so the
        pipeline still works for URLs or test fixtures.
        """
        path = Path(image_source)
        if path.is_file():
            data = path.read_bytes()
        else:
            data = image_source.encode()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _detect_milestones(image_source: str) -> list[str]:
        """Return mock milestone labels derived from the image source."""
        all_milestones = [
            "foundation_complete",
            "framing_complete",
            "roofing_complete",
            "electrical_rough_in",
            "plumbing_rough_in",
        ]
        index = sum(ord(c) for c in image_source) % len(all_milestones)
        return all_milestones[: index + 1]
