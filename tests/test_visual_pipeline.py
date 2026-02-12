"""Tests for VisualForensicsPipeline – image analysis pipeline."""

import pytest

from visual_pipeline.pipeline import VisualForensicsPipeline


@pytest.fixture
def pipeline():
    """Returns a fresh VisualForensicsPipeline."""
    return VisualForensicsPipeline()


# ✅ TEST: Submit image
def test_submit_image(pipeline):
    """submit_image should create a job with pending status."""
    job = pipeline.submit_image(
        project_id="P001",
        image_source="site_photo_001.jpg",
    )
    assert job.project_id == "P001"
    assert job.image_source == "site_photo_001.jpg"
    assert job.status == "pending"


# ✅ TEST: Get job status
def test_get_job_status(pipeline):
    """get_job_status should return status info for a submitted job."""
    job = pipeline.submit_image("P001", "photo.jpg")
    status = pipeline.get_job_status(job.job_id)
    assert status["job_id"] == job.job_id
    assert status["status"] == "pending"
    assert status["project_id"] == "P001"


# ✅ TEST: Get project jobs
def test_get_project_jobs(pipeline):
    """get_project_jobs should return all jobs for a project."""
    pipeline.submit_image("P001", "photo1.jpg")
    pipeline.submit_image("P001", "photo2.jpg")
    pipeline.submit_image("P002", "photo3.jpg")

    jobs = pipeline.get_project_jobs("P001")
    assert len(jobs) == 2
    assert all(j.project_id == "P001" for j in jobs)


# ✅ TEST: Process image
def test_process_image(pipeline):
    """process_image should produce an ImageJobResult with milestones."""
    job = pipeline.submit_image("P001", "foundation_photo.jpg")
    result = pipeline.process_image(job.job_id)

    assert result.job_id == job.job_id
    assert result.project_id == "P001"
    assert len(result.milestones_detected) > 0
    assert result.duplicate_hash is not None
    assert len(result.duplicate_hash) == 64
    assert result.ocr_text is not None
    assert job.status == "completed"
