"""Tests for TaskQueue – in-process background task queue."""

import pytest

from workers.task_queue import TaskQueue, JobStatus


@pytest.fixture
def queue():
    """Returns a TaskQueue with a simple echo handler registered."""
    q = TaskQueue(max_retries=3)
    q.register("echo", lambda payload: payload)
    return q


# ✅ TEST: Submit a job
def test_submit_job(queue):
    """submit should create a job with PENDING status."""
    job = queue.submit("echo", {"msg": "hello"})
    assert job.status == JobStatus.PENDING
    assert job.task_name == "echo"
    assert job.payload == {"msg": "hello"}


# ✅ TEST: Process a job successfully
def test_process_job_success(queue):
    """process should run the handler and mark the job COMPLETED."""
    job = queue.submit("echo", {"msg": "hello"})
    result = queue.process(job.job_id)
    assert result.status == JobStatus.COMPLETED
    assert result.result == {"msg": "hello"}
    assert result.error is None


# ✅ TEST: Process job failure and retry
def test_process_job_failure_retry(queue):
    """A failing handler should increment retry_count and set RETRYING."""
    queue.register("fail", lambda p: (_ for _ in ()).throw(ValueError("boom")))
    job = queue.submit("fail", {})
    result = queue.process(job.job_id)
    assert result.status == JobStatus.RETRYING
    assert result.retry_count == 1
    assert "boom" in result.error


# ✅ TEST: Dead letter after max retries
def test_dead_letter_after_max_retries(queue):
    """After max_retries failures, job should go to DEAD_LETTER."""
    queue.register("fail", lambda p: (_ for _ in ()).throw(RuntimeError("fail")))
    job = queue.submit("fail", {})
    for _ in range(3):
        queue.process(job.job_id)
    assert job.status == JobStatus.DEAD_LETTER


# ✅ TEST: Process all pending
def test_process_all_pending(queue):
    """process_all_pending should process all PENDING jobs."""
    queue.submit("echo", {"a": 1})
    queue.submit("echo", {"b": 2})
    results = queue.process_all_pending()
    assert len(results) == 2
    assert all(r.status == JobStatus.COMPLETED for r in results)


# ✅ TEST: Get job stats
def test_get_job_stats(queue):
    """get_job_stats should return counts grouped by status."""
    queue.submit("echo", {"a": 1})
    queue.submit("echo", {"b": 2})
    queue.process_all_pending()
    stats = queue.get_job_stats()
    assert stats["completed"] == 2
    assert stats["pending"] == 0


# ✅ TEST: Unregistered task fails
def test_unregistered_task_fails(queue):
    """Processing a job with no registered handler should raise ValueError."""
    job = queue.submit("unknown_task", {})
    with pytest.raises(ValueError, match="No handler registered"):
        queue.process(job.job_id)
