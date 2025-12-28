import pytest
from core.gap_detector import ComplianceGapEngine
from core.models import GapAnalysisResponse

# 🏗️ FIXTURE: Shared engine setup
@pytest.fixture
def structural_engine():
    """Returns a pre-configured engine for structural projects."""
    return ComplianceGapEngine(project_type="structural")

# ✅ TEST: Partial Milestone Detection
def test_detect_gaps_partial_completion(structural_engine):
    """Checks that only finding 'Foundation' triggers a missing 'Structural Steel' gap."""
    found_milestones = ["Foundation"]
    
    result = structural_engine.detect_gaps(found_milestones)
    
    assert isinstance(result, GapAnalysisResponse)
    assert result.compliance_score < 100
    assert result.gap_count > 0
    # Verify the logic correctly identified the missing steel
    missing_names = [m.milestone for m in result.missing_milestones]
    assert "Structural Steel" in missing_names

# ✅ TEST: 100% Compliance
def test_detect_gaps_full_compliance(structural_engine):
    """Ensures a perfect score when all required milestones are provided."""
    # This must match the items in your core.constants.MILESTONES["structural"]
    all_milestones = ["Foundation", "Structural Steel", "Fireproofing"]
    
    result = structural_engine.detect_gaps(all_milestones)
    
    assert result.compliance_score == 100
    assert len(result.missing_milestones) == 0
    assert result.next_priority == "Fully Compliant"

# ❌ TEST: Invalid Input Handling
def test_engine_empty_input(structural_engine):
    """Ensures the engine doesn't crash if zero milestones are found."""
    result = structural_engine.detect_gaps([])
    assert result.compliance_score == 0
    assert result.risk_score == 100
