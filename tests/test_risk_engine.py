"""Tests for DeterministicRiskEngine – risk scoring for NYC DOB compliance."""

import pytest

from risk_engine.engine import DeterministicRiskEngine


@pytest.fixture
def engine():
    """Returns a pre-configured risk engine."""
    return DeterministicRiskEngine(model_version="1.0.0")


# ✅ TEST: Zero risk with all defaults
def test_zero_risk_all_defaults(engine):
    """All default inputs should produce a risk_score near 0."""
    result = engine.score_project()
    # building_risk_score for commercial/1-story gives a small nonzero base
    assert result.risk_score <= 5


# ✅ TEST: Maximum risk
def test_maximum_risk(engine):
    """Worst-case inputs should produce a risk_score close to 100."""
    result = engine.score_project(
        violation_classes=["Class C"],
        permit_age_days=900,
        inspection_failures=10,
        inspection_total=10,
        milestone_delay_days=120,
        complaint_count_90d=10,
        prior_stop_work_orders=5,
        building_type="residential",
        stories=50,
        contractor_violation_rate=1.0,
    )
    assert result.risk_score >= 90


# ✅ TEST: Class C violation score
def test_class_c_violation_score(engine):
    """Class C should give the maximum violation severity score of 30."""
    score = engine._violation_severity_score(["Class C"])
    assert score == 30.0


# ✅ TEST: Class B violation score
def test_class_b_violation_score(engine):
    """Class B should give a violation severity score of 20."""
    score = engine._violation_severity_score(["Class B"])
    assert score == 20.0


# ✅ TEST: Class A violation score
def test_class_a_violation_score(engine):
    """Class A should give a violation severity score of 10."""
    score = engine._violation_severity_score(["Class A"])
    assert score == 10.0


# ✅ TEST: Permit age scoring
def test_permit_age_scoring(engine):
    """Permit age linearly scales between 180 and 720 days."""
    assert engine._permit_age_score(100) == 0.0
    assert engine._permit_age_score(180) == 0.0
    assert engine._permit_age_score(720) == 15.0
    mid = engine._permit_age_score(450)
    assert 0.0 < mid < 15.0


# ✅ TEST: Inspection failure rate
def test_inspection_failure_rate(engine):
    """Failure/total ratio affects the inspection failure score."""
    assert engine._inspection_failure_score(0, 10) == 0.0
    assert engine._inspection_failure_score(10, 10) == 15.0
    half = engine._inspection_failure_score(5, 10)
    assert half == pytest.approx(7.5)


# ✅ TEST: Deterministic reproducibility
def test_deterministic_reproducibility(engine):
    """Same inputs must produce identical risk_score across two calls."""
    kwargs = dict(
        violation_classes=["Class B"],
        permit_age_days=400,
        inspection_failures=3,
        inspection_total=10,
        milestone_delay_days=30,
        complaint_count_90d=2,
        prior_stop_work_orders=1,
        building_type="residential",
        stories=10,
        contractor_violation_rate=0.3,
    )
    r1 = engine.score_project(**kwargs)
    r2 = engine.score_project(**kwargs)
    assert r1.risk_score == r2.risk_score
    assert r1.fine_exposure_estimate == r2.fine_exposure_estimate


# ✅ TEST: Risk drivers ordering
def test_risk_drivers_ordering(engine):
    """Risk drivers should be sorted in descending order of contribution."""
    result = engine.score_project(
        violation_classes=["Class C"],
        permit_age_days=500,
        inspection_failures=5,
        inspection_total=10,
    )
    assert len(result.risk_drivers) > 0
    # The first driver should be the highest contributing factor
    assert result.risk_drivers[0] == "violation_severity_score"


# ✅ TEST: Model version stored
def test_model_version_stored(engine):
    """model_version should be present in the output."""
    result = engine.score_project()
    assert result.model_version == "1.0.0"


# ✅ TEST: Features snapshot stored
def test_features_snapshot_stored(engine):
    """All input parameters should be stored in features_snapshot."""
    result = engine.score_project(
        violation_classes=["Class A"],
        permit_age_days=200,
        building_type="residential",
        stories=5,
    )
    snap = result.features_snapshot
    assert snap["violation_classes"] == ["Class A"]
    assert snap["permit_age_days"] == 200
    assert snap["building_type"] == "residential"
    assert snap["stories"] == 5
    assert "inspection_failures" in snap
    assert "contractor_violation_rate" in snap


# ✅ TEST: Stop-work probability for high risk
def test_stop_work_probability_high_risk(engine):
    """High risk score should yield a high stop-work probability."""
    result = engine.score_project(
        violation_classes=["Class C"],
        permit_age_days=900,
        inspection_failures=10,
        inspection_total=10,
        milestone_delay_days=120,
        complaint_count_90d=10,
        prior_stop_work_orders=5,
        building_type="residential",
        stories=50,
        contractor_violation_rate=1.0,
    )
    assert result.stop_work_probability_30d > 0.8


# ✅ TEST: Stop-work probability for low risk
def test_stop_work_probability_low_risk(engine):
    """Low risk score should yield a low stop-work probability."""
    result = engine.score_project()
    assert result.stop_work_probability_30d < 0.3


# ✅ TEST: Fine exposure calculation
def test_fine_exposure_calculation(engine):
    """Verify fine amounts per violation class."""
    result = engine.score_project(
        violation_classes=["Class A", "Class C"],
        building_type="residential",
    )
    # Class A = $2,500, Class C = $25,000 → total $27,500 (no commercial multiplier)
    assert result.fine_exposure_estimate == pytest.approx(27_500.0)


# ✅ TEST: Explain method
def test_explain_method(engine):
    """explain() should return a breakdown dict with component scores."""
    result = engine.score_project(
        violation_classes=["Class B"],
        permit_age_days=400,
    )
    breakdown = engine.explain(result)
    assert "component_scores" in breakdown
    assert "component_sum" in breakdown
    assert "model_version" in breakdown
    assert breakdown["model_version"] == "1.0.0"
    assert breakdown["risk_score"] == result.risk_score
