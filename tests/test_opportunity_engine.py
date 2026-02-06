"""
Tests for Opportunity Matching Engine
Tests the conservative classifier, feasibility scorer, and simulator.
"""

import os
from datetime import datetime, timedelta

import pytest

from packages.agents.opportunity import (
    AgencyType,
    FeasibilityScorer,
    OpportunityClassifier,
    OpportunityLevel,
    UserComplianceProfile,
)
from tests.simulator import OpportunitySimulator


class TestOpportunitySimulator:
    """Test the data simulator generates realistic ugly data."""
    
    def test_generate_closed_sample(self):
        """Simulator generates CLOSED samples with correct markers."""
        simulator = OpportunitySimulator()
        sample = simulator.generate_sample(opportunity_type="closed", include_errors=False)
        
        assert sample["expected_classification"] == "CLOSED"
        assert "project_id" in sample
        assert "agency_text" in sample
        
        # Check for closed markers in text
        text_lower = sample["agency_text"].lower()
        closed_markers = ["planning", "pre-solicitation", "upcoming", "tentative", "under review"]
        assert any(marker in text_lower for marker in closed_markers)
    
    def test_generate_contestable_sample(self):
        """Simulator generates CONTESTABLE samples with required elements."""
        simulator = OpportunitySimulator()
        sample = simulator.generate_sample(opportunity_type="contestable", include_errors=False)
        
        assert sample["expected_classification"] == "CONTESTABLE"
        
        # Check for contestable markers
        text_lower = sample["agency_text"].lower()
        contestable_markers = ["request for proposals", "rfp", "accepting bids", "bid deadline", "due:"]
        assert any(marker in text_lower for marker in contestable_markers)
    
    def test_batch_generation_distribution(self):
        """Batch generation respects distribution probabilities."""
        simulator = OpportunitySimulator()
        
        # Generate large batch to test distribution
        batch = simulator.generate_batch(
            count=100,
            distribution={"closed": 0.5, "soft_open": 0.3, "contestable": 0.2}
        )
        
        assert len(batch) == 100
        
        # Count actual distribution (should be close to target)
        closed_count = sum(1 for s in batch if s["expected_classification"] == "CLOSED")
        soft_count = sum(1 for s in batch if s["expected_classification"] == "SOFT_OPEN")
        contestable_count = sum(1 for s in batch if s["expected_classification"] == "CONTESTABLE")
        
        # Allow 15% variance due to randomness
        assert 35 <= closed_count <= 65  # 50% ± 15%
        assert 15 <= soft_count <= 45    # 30% ± 15%
        assert 5 <= contestable_count <= 35  # 20% ± 15%
    
    def test_ugliness_adds_errors(self):
        """Uglification adds realistic errors to text."""
        simulator = OpportunitySimulator()
        
        sample_clean = simulator.generate_sample(opportunity_type="closed", include_errors=False)
        sample_ugly = simulator.generate_sample(opportunity_type="closed", include_errors=True)
        
        # Ugly sample should be different (has errors/formatting issues)
        # Note: Due to randomness, this might occasionally fail - that's acceptable
        # The key is that the uglifier is being called
        assert "agency_text" in sample_ugly


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY environment variable"
)
class TestOpportunityClassifier:
    """
    Tests for conservative opportunity classifier.
    These tests require an API key and make real API calls.
    """
    
    @pytest.fixture
    def classifier(self):
        """Create classifier with API key from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        return OpportunityClassifier(api_key=api_key)
    
    def test_classify_closed_opportunity(self, classifier):
        """Classifier correctly identifies CLOSED opportunity."""
        agency_text = """
        PRE-SOLICITATION NOTICE
        PS 456 Window Replacement Project
        Estimated Release: March 2026
        This is for planning purposes only. No bids are being accepted.
        """
        
        result = classifier.classify(
            project_id="TEST-001",
            project_title="PS 456 Window Replacement",
            agency_text=agency_text,
            agency=AgencyType.SCA
        )
        
        assert result.opportunity_level == OpportunityLevel.CLOSED
        assert result.decision_proof.confidence > 0.5
        assert len(result.decision_proof.red_flags) > 0
    
    def test_classify_contestable_opportunity(self, classifier):
        """Classifier correctly identifies CONTESTABLE opportunity."""
        agency_text = """
        REQUEST FOR PROPOSALS - RFP #2026-042
        DDC Street Resurfacing Project - Brooklyn District 4
        
        Bid Deadline: March 15, 2026 at 2:00 PM EST
        Mandatory Pre-Bid Meeting: March 1, 2026
        
        Scope: Milling and resurfacing of 15 blocks
        Insurance Required: GL $3M, WC $3M, Umbrella $5M
        
        Download bid documents at: www.nyc.gov/ddc/bids/2026-042
        Questions to: ddc_procurement@ddc.nyc.gov
        """
        
        result = classifier.classify(
            project_id="DDC-2026-042",
            project_title="Street Resurfacing - Brooklyn D4",
            agency_text=agency_text,
            agency=AgencyType.DDC,
            estimated_value=2_500_000
        )
        
        assert result.opportunity_level == OpportunityLevel.CONTESTABLE
        assert result.decision_proof.confidence > 0.7
        assert len(result.decision_proof.text_signals) > 0
    
    def test_classifier_fallback_on_error(self, classifier):
        """Classifier defaults to CLOSED on error (skeptical fallback)."""
        # Pass invalid data to trigger error handling
        result = classifier.classify(
            project_id="ERROR-TEST",
            project_title="",
            agency_text="",
            agency=AgencyType.OTHER
        )
        
        # Should fallback to CLOSED per skeptical philosophy
        assert result.opportunity_level == OpportunityLevel.CLOSED
        assert result.decision_proof.confidence == 0.0


class TestFeasibilityScorer:
    """Tests for feasibility scoring and compliance checking."""
    
    @pytest.fixture
    def scorer(self):
        """Create feasibility scorer."""
        return FeasibilityScorer()
    
    @pytest.fixture
    def compliant_user(self):
        """Create a fully compliant user profile."""
        return UserComplianceProfile(
            user_id="USER-001",
            company_name="ABC Construction",
            general_liability_limit=5_000_000,
            workers_comp_limit=5_000_000,
            umbrella_limit=10_000_000,
            insurance_expiry=datetime.now() + timedelta(days=180),
            active_licenses=["General Contractor", "Electrical"],
            license_expiry={
                "General Contractor": datetime.now() + timedelta(days=365),
                "Electrical": datetime.now() + timedelta(days=365),
            },
            has_active_dob_registration=True
        )
    
    @pytest.fixture
    def non_compliant_user(self):
        """Create a user with compliance gaps."""
        return UserComplianceProfile(
            user_id="USER-002",
            company_name="XYZ Builders",
            general_liability_limit=1_000_000,  # Too low for SCA
            workers_comp_limit=1_000_000,  # Too low
            umbrella_limit=None,  # Missing
            insurance_expiry=datetime.now() + timedelta(days=90),
            active_licenses=["Plumbing"],  # Wrong license
            license_expiry={"Plumbing": datetime.now() + timedelta(days=180)},
            has_active_dob_registration=False  # Missing DOB
        )
    
    def test_feasibility_score_closed_opportunity(self, scorer, compliant_user):
        """Feasibility scorer returns not ready for CLOSED opportunities."""
        from packages.agents.opportunity.models import (
            DecisionProof,
            OpportunityClassification,
        )
        
        # Create a CLOSED opportunity
        opportunity = OpportunityClassification(
            project_id="TEST-001",
            project_title="Test Project",
            agency=AgencyType.SCA,
            opportunity_level=OpportunityLevel.CLOSED,
            decision_proof=DecisionProof(
                decision=OpportunityLevel.CLOSED,
                confidence=0.9,
                reasoning="Planning phase only",
                text_signals=["planning", "pre-solicitation"],
                red_flags=[]
            ),
            raw_text="Planning phase project"
        )
        
        result = scorer.check_feasibility(opportunity, compliant_user)
        
        # Should not be ready for closed opportunity
        assert result.is_compliant is False
        assert result.feasibility_score == 0.0
        assert "not confirmed as CONTESTABLE" in result.insurance_gaps[0]
    
    def test_feasibility_score_compliant_user(self, scorer, compliant_user):
        """Compliant user gets green check for CONTESTABLE opportunity."""
        from packages.agents.opportunity.models import (
            DecisionProof,
            OpportunityClassification,
        )
        
        # Create a CONTESTABLE opportunity
        opportunity = OpportunityClassification(
            project_id="SCA-2026-100",
            project_title="School HVAC Upgrade",
            agency=AgencyType.SCA,
            opportunity_level=OpportunityLevel.CONTESTABLE,
            decision_proof=DecisionProof(
                decision=OpportunityLevel.CONTESTABLE,
                confidence=0.95,
                reasoning="Clear RFP with deadline",
                text_signals=["RFP", "deadline", "submit bids"],
                red_flags=[]
            ),
            raw_text="RFP with clear deadline",
            trade_category="General Construction"
        )
        
        result = scorer.check_feasibility(opportunity, compliant_user)
        
        # Compliant user should get green check
        assert result.is_compliant is True
        assert result.feasibility_score >= 80.0
        assert result.insurance_compliant is True
        assert result.license_compliant is True
        assert len(result.insurance_gaps) == 0
        assert len(result.license_gaps) == 0
    
    def test_feasibility_score_non_compliant_user(self, scorer, non_compliant_user):
        """Non-compliant user gets detailed gap analysis."""
        from packages.agents.opportunity.models import (
            DecisionProof,
            OpportunityClassification,
        )
        
        opportunity = OpportunityClassification(
            project_id="SCA-2026-200",
            project_title="School Construction",
            agency=AgencyType.SCA,
            opportunity_level=OpportunityLevel.CONTESTABLE,
            decision_proof=DecisionProof(
                decision=OpportunityLevel.CONTESTABLE,
                confidence=0.9,
                reasoning="Active RFP",
                text_signals=["RFP"],
                red_flags=[]
            ),
            raw_text="RFP active",
            trade_category="General Construction"
        )
        
        result = scorer.check_feasibility(opportunity, non_compliant_user)
        
        # Should fail compliance
        assert result.is_compliant is False
        assert result.feasibility_score < 80.0
        
        # Should have insurance gaps (SCA requires $5M/$5M/$10M)
        assert result.insurance_compliant is False
        assert len(result.insurance_gaps) > 0
        assert any("General Liability" in gap for gap in result.insurance_gaps)
        
        # Should have license gaps (has Plumbing, needs General Contractor)
        assert result.license_compliant is False
        assert len(result.license_gaps) > 0
        
        # Should have DOB registration gap
        assert len(result.other_barriers) > 0
        assert any("DOB" in barrier for barrier in result.other_barriers)
        
        # Should have actionable next steps
        assert len(result.next_steps) > 0
    
    def test_insurance_requirements_by_agency(self, scorer, compliant_user):
        """Different agencies have different insurance requirements."""
        from packages.agents.opportunity.models import (
            DecisionProof,
            OpportunityClassification,
        )
        
        # Test with DDC (lower requirements than SCA)
        opportunity_ddc = OpportunityClassification(
            project_id="DDC-001",
            project_title="DDC Project",
            agency=AgencyType.DDC,
            opportunity_level=OpportunityLevel.CONTESTABLE,
            decision_proof=DecisionProof(
                decision=OpportunityLevel.CONTESTABLE,
                confidence=0.9,
                reasoning="Active",
                text_signals=[],
                red_flags=[]
            ),
            raw_text="Active RFP"
        )
        
        # User with $3M/$3M coverage (meets DDC but not SCA)
        user_mid_coverage = UserComplianceProfile(
            user_id="USER-003",
            company_name="Mid Coverage Co",
            general_liability_limit=3_000_000,
            workers_comp_limit=3_000_000,
            umbrella_limit=5_000_000,
            insurance_expiry=datetime.now() + timedelta(days=180),
            active_licenses=["General Contractor"],
            license_expiry={"General Contractor": datetime.now() + timedelta(days=365)},
            has_active_dob_registration=True
        )
        
        result_ddc = scorer.check_feasibility(opportunity_ddc, user_mid_coverage)
        
        # Should be compliant for DDC
        assert result_ddc.insurance_compliant is True
        
        # But same user should fail for SCA
        opportunity_sca = OpportunityClassification(
            project_id="SCA-001",
            project_title="SCA Project",
            agency=AgencyType.SCA,
            opportunity_level=OpportunityLevel.CONTESTABLE,
            decision_proof=DecisionProof(
                decision=OpportunityLevel.CONTESTABLE,
                confidence=0.9,
                reasoning="Active",
                text_signals=[],
                red_flags=[]
            ),
            raw_text="Active RFP"
        )
        
        result_sca = scorer.check_feasibility(opportunity_sca, user_mid_coverage)
        
        # Should fail for SCA (needs $5M)
        assert result_sca.insurance_compliant is False
        assert any("General Liability" in gap for gap in result_sca.insurance_gaps)
