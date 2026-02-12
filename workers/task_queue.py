"""In-process background task queue – no external broker required."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str
    payload: dict = Field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    tenant_id: str = "default"


class TaskQueue:
    """Simple in-process task queue with retry and dead-letter support."""

    def __init__(self, max_retries: int = 3) -> None:
        self._jobs: dict[str, Job] = {}
        self._handlers: dict[str, Callable] = {}
        self._max_retries = max_retries

    def register(self, task_name: str, handler: Callable) -> None:
        """Register a handler function for a given task type."""
        self._handlers[task_name] = handler

    def submit(self, task_name: str, payload: dict, tenant_id: str = "default") -> Job:
        """Create and enqueue a new job."""
        job = Job(
            task_name=task_name,
            payload=payload,
            max_retries=self._max_retries,
            tenant_id=tenant_id,
        )
        self._jobs[job.job_id] = job
        return job

    def process(self, job_id: str) -> Job:
        """Execute the handler for a single job, managing status and retries."""
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job {job_id} not found")

        handler = self._handlers.get(job.task_name)
        if handler is None:
            raise ValueError(f"No handler registered for task '{job.task_name}'")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)

        try:
            job.result = handler(job.payload)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.error = None
        except Exception as exc:  # noqa: BLE001
            job.error = str(exc)
            job.retry_count += 1
            if job.retry_count < job.max_retries:
                job.status = JobStatus.RETRYING
            else:
                job.status = JobStatus.DEAD_LETTER
            job.completed_at = datetime.now(timezone.utc)

        return job

    def process_all_pending(self) -> list[Job]:
        """Process every job that is PENDING or RETRYING."""
        targets = [
            j
            for j in self._jobs.values()
            if j.status in (JobStatus.PENDING, JobStatus.RETRYING)
        ]
        return [self.process(j.job_id) for j in targets]

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def get_jobs_by_status(self, status: JobStatus) -> list[Job]:
        return [j for j in self._jobs.values() if j.status == status]

    def get_dead_letter_jobs(self) -> list[Job]:
        return self.get_jobs_by_status(JobStatus.DEAD_LETTER)

    def get_job_stats(self) -> dict:
        """Return a count of jobs grouped by status."""
        stats: dict[str, int] = {s.value: 0 for s in JobStatus}
        for job in self._jobs.values():
            stats[job.status.value] += 1
        return stats
