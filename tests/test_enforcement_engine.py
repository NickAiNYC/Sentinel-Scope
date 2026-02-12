"""Tests for EnforcementEngine – enforcement forecasting."""

import pytest

from core.enforcement_engine import EnforcementEngine


@pytest.fixture
def engine():
    """Returns a fresh EnforcementEngine."""
    return EnforcementEngine()


# ✅ TEST: High risk enforcement
def test_high_risk_enforcement(engine):
    """Risk 85+ should give emergency/order level escalation."""
    result = engine.forecast_enforcement(
        risk_score=90,
        violation_classes=["Class C"],
    )
    assert result["escalation_level"] in ("emergency", "order")


# ✅ TEST: Low risk enforcement
def test_low_risk_enforcement(engine):
    """Risk < 30 should give notice or warning level."""
    result = engine.forecast_enforcement(
        risk_score=15,
        violation_classes=["Class A"],
    )
    assert result["escalation_level"] in ("notice", "warning")


# ✅ TEST: Class C increases stop-work probability
def test_class_c_increases_stop_work(engine):
    """Class C violations should raise stop-work probability."""
    result_no_c = engine.forecast_enforcement(
        risk_score=60,
        violation_classes=["Class A"],
    )
    result_with_c = engine.forecast_enforcement(
        risk_score=60,
        violation_classes=["Class C"],
    )
    assert result_with_c["stop_work_probability_30d"] > result_no_c["stop_work_probability_30d"]


# ✅ TEST: Prior SWO increases probability
def test_prior_swo_increases_probability(engine):
    """Prior stop-work orders should increase stop-work probability."""
    result_no_swo = engine.forecast_enforcement(
        risk_score=60,
        violation_classes=["Class B"],
        prior_stop_work_orders=0,
    )
    result_with_swo = engine.forecast_enforcement(
        risk_score=60,
        violation_classes=["Class B"],
        prior_stop_work_orders=3,
    )
    assert result_with_swo["stop_work_probability_30d"] > result_no_swo["stop_work_probability_30d"]


# ✅ TEST: Timeline for high risk
def test_timeline_high_risk(engine):
    """High risk should produce a short timeline (7 days)."""
    result = engine.forecast_enforcement(
        risk_score=85,
        violation_classes=["Class C"],
    )
    assert result["timeline_days"] == 7


# ✅ TEST: Timeline for low risk
def test_timeline_low_risk(engine):
    """Low risk should produce a longer timeline (90 days)."""
    result = engine.forecast_enforcement(
        risk_score=20,
        violation_classes=["Class A"],
    )
    assert result["timeline_days"] == 90


# ✅ TEST: Recommended actions present
def test_recommended_actions_present(engine):
    """Forecast should include recommended actions."""
    result = engine.forecast_enforcement(
        risk_score=50,
        violation_classes=["Class B"],
    )
    assert len(result["recommended_actions"]) > 0
