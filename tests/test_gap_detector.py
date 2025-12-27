import pytest
from core.gap_detector import detect_gaps
from core.models import GapAnalysisResponse

def test_detect_gaps_structural_success():
    """Validates that foundation and steel detection triggers correct gap analysis"""
    found_milestones = ["Foundation"]
    project_type = "Structural"
    
    result = detect_gaps(found_milestones, project_type)
    
    assert isinstance(result, GapAnalysisResponse)
    assert result.compliance_score < 100  # Should have gaps if only foundation is found
    assert any(m.milestone == "Structural Steel" for m in result.missing_milestones)

def test_detect_gaps_full_compliance():
    """Validates 100% score when all milestones are present"""
    # This assumes your MILESTONES constant for Structural includes these two
    found_milestones = ["Foundation", "Structural Steel"]
    project_type = "Structural"
    
    result = detect_gaps(found_milestones, project_type)
    
    assert result.compliance_score == 100
    assert len(result.missing_milestones) == 0
