"""Tests for ForensicsEngine – compliance snapshot archival and replay."""

import pytest
from datetime import datetime, timezone, timedelta

from data_forensics.forensics_engine import ForensicsEngine


@pytest.fixture
def forensics():
    """Returns a fresh ForensicsEngine."""
    return ForensicsEngine()


# ✅ TEST: Archive ingestion creates a snapshot with hash
def test_archive_ingestion(forensics):
    """archive_ingestion should return a snapshot with a valid SHA-256 hash."""
    snapshot = forensics.archive_ingestion(
        project_id="P001",
        source="test",
        raw_payload={"key": "value"},
    )
    assert snapshot.project_id == "P001"
    assert len(snapshot.data_hash) == 64
    assert snapshot.snapshot_id is not None


# ✅ TEST: Retrieve snapshot by ID
def test_get_snapshot(forensics):
    """get_snapshot should retrieve a snapshot by its ID."""
    snapshot = forensics.archive_ingestion(
        project_id="P001",
        source="test",
        raw_payload={"data": 1},
    )
    retrieved = forensics.get_snapshot(snapshot.snapshot_id)
    assert retrieved is not None
    assert retrieved.snapshot_id == snapshot.snapshot_id


# ✅ TEST: Get all snapshots for a project
def test_get_project_snapshots(forensics):
    """get_project_snapshots should return all snapshots for a project."""
    forensics.archive_ingestion("P001", "src1", {"a": 1})
    forensics.archive_ingestion("P001", "src2", {"b": 2})
    forensics.archive_ingestion("P002", "src3", {"c": 3})

    snapshots = forensics.get_project_snapshots("P001")
    assert len(snapshots) == 2
    assert all(s.project_id == "P001" for s in snapshots)


# ✅ TEST: Reconstruct state at a given time
def test_reconstruct_state_at(forensics):
    """reconstruct_state_at should return the latest snapshot <= at_time."""
    s1 = forensics.archive_ingestion("P001", "src1", {"version": 1})

    # Use a time in the future to ensure we get the snapshot
    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    result = forensics.reconstruct_state_at("P001", future)
    assert result is not None
    assert result.snapshot_id == s1.snapshot_id


# ✅ TEST: Verify integrity passes
def test_verify_integrity(forensics):
    """verify_integrity should pass for an unmodified snapshot."""
    snapshot = forensics.archive_ingestion(
        project_id="P001",
        source="test",
        raw_payload={"important": "data"},
    )
    assert forensics.verify_integrity(snapshot.snapshot_id) is True


# ✅ TEST: Verify integrity fails for tampered data
def test_verify_integrity_tampered(forensics):
    """verify_integrity should fail when raw_payload has been modified."""
    snapshot = forensics.archive_ingestion(
        project_id="P001",
        source="test",
        raw_payload={"important": "data"},
    )
    # Tamper with the stored payload directly
    forensics._snapshots[snapshot.snapshot_id] = snapshot.model_copy(
        update={"raw_payload": {"important": "tampered"}, "data_hash": snapshot.data_hash}
    )
    assert forensics.verify_integrity(snapshot.snapshot_id) is False


# ✅ TEST: Replay risk score
def test_replay_risk_score(forensics):
    """replay_risk_score should replay scoring from archived data."""

    class MockRiskEngine:
        def score(self, features):
            from core.compliance_models import RiskAssessment
            from datetime import datetime, timezone
            return RiskAssessment(
                risk_score=42,
                stop_work_probability_30d=0.3,
                insurance_escalation_probability=0.2,
                fine_exposure_estimate=5000.0,
                risk_drivers=["test"],
                model_version="1.0.0",
                scored_at=datetime.now(timezone.utc),
                features_snapshot=features,
            )

    snapshot = forensics.archive_ingestion("P001", "test", {"data": "value"})
    result = forensics.replay_risk_score(snapshot.snapshot_id, MockRiskEngine())
    assert result is not None
    assert result.risk_score == 42


# ✅ TEST: Empty project returns empty list
def test_empty_project_returns_empty_list(forensics):
    """get_project_snapshots should return an empty list for unknown project."""
    assert forensics.get_project_snapshots("NONEXISTENT") == []
