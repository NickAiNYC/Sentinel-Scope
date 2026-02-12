"""
End-to-end construction audit test: Complete site → report pipeline.

Tests the full flow from site photo analysis through the 5-agent
architecture to final DecisionProof.
"""

import pytest

from core.drone_analytics_bridge import DroneAnalyticsBridge
from core.progress_tracker_ai import ProgressTrackerAI
from core.safety_violation_detector import SafetyViolationDetector, ViolationType
from packages.ll11_facade_vision_bridge import FacadeCondition, LL11FacadeVisionBridge
from packages.ll149_inspector_bridge import LL149InspectorBridge, SuperintendentStatus
from packages.ll152_gas_tracker_bridge import GasPipingStatus, LL152GasTrackerBridge
from packages.vision_agent_bridge import (
    DecisionProofRecord,
    VisionAgentBridge,
)


class TestEndToEndConstructionAudit:
    """Full pipeline: photos → vision → bridges → proof."""

    @pytest.fixture
    def bridge(self):
        return VisionAgentBridge()

    @pytest.fixture
    def site_findings(self):
        """Simulated VisionAgent output for a construction site."""
        return [
            {
                "name": "no fall protection 3rd floor",
                "confidence": 0.95,
                "type": "safety",
            },
            {
                "name": "crack on facade >1/4 inch",
                "confidence": 0.94,
                "type": "defect",
            },
            {
                "name": "gas piping installation",
                "confidence": 0.90,
                "type": "mep",
            },
            {
                "name": "Worker-123 no hard hat",
                "confidence": 0.88,
                "type": "safety",
            },
            {
                "name": "excavation area",
                "milestone": "EXCAVATION",
                "confidence": 1.0,
                "volume_cy": 2340,
            },
            {
                "name": "superstructure frame",
                "milestone": "SUPERSTRUCTURE",
                "confidence": 0.30,
            },
        ]

    @pytest.fixture
    def dob_violations(self):
        return [
            {
                "violation_number": "V-2026-001",
                "violation_type": "Class B",
                "issue_date": "2026-01-20",
            },
        ]

    def test_full_pipeline_produces_proof(self, bridge, site_findings, dob_violations):
        """End-to-end: submit analysis and get sealed DecisionProof."""
        proof = bridge.run_full_pipeline(
            bbl="1012650001",
            address="350 Fifth Avenue, New York, NY 10118",
            images_processed=12,
            findings=site_findings,
            violations=[],
            dob_violations=dob_violations,
            compliance_score=62.0,
            risk_score=78.0,
        )

        assert proof is not None
        assert isinstance(proof, DecisionProofRecord)
        assert proof.bbl == "1012650001"
        assert len(proof.sha256_hash) == 64
        assert proof.compliance_score == 62.0
        assert proof.risk_score == 78.0
        assert len(proof.agent_chain) == 5

    def test_ll149_in_pipeline(self, site_findings):
        """LL149 bridge detects superintendent absence."""
        bridge = LL149InspectorBridge()
        result = bridge.analyze_site("1012650001", site_findings, permit_type="NB")
        assert result.superintendent_status == SuperintendentStatus.NOT_DETECTED
        assert result.violation_probability >= 0.87

    def test_ll152_in_pipeline(self, site_findings):
        """LL152 bridge detects gas piping without sticker."""
        bridge = LL152GasTrackerBridge()
        result = bridge.analyze_site("1012650001", site_findings)
        assert result.gas_piping_status == GasPipingStatus.PIPING_DETECTED_NO_STICKER

    def test_ll11_in_pipeline(self, site_findings):
        """LL11 bridge detects facade crack."""
        bridge = LL11FacadeVisionBridge()
        result = bridge.analyze_facade("1012650001", site_findings, year_built=1940)
        assert result.facade_condition == FacadeCondition.UNSAFE
        assert result.critical_exam_required is True
        assert result.pre_1950_multiplier == 2.8

    def test_safety_detector_in_pipeline(self, site_findings):
        """Safety detector catches fall protection and PPE violations."""
        detector = SafetyViolationDetector()
        result = detector.analyze("1012650001", site_findings)
        detected_types = {v.violation_type for v in result.violations}
        assert ViolationType.FALL_PROTECTION in detected_types
        assert ViolationType.PPE_NONCOMPLIANCE in detected_types
        assert result.overall_risk == "CRITICAL"

    def test_progress_tracker_in_pipeline(self, site_findings):
        """Progress tracker measures milestone completion."""
        tracker = ProgressTrackerAI()
        scheduled = {"EXCAVATION": 100.0, "SUPERSTRUCTURE": 50.0}
        report = tracker.analyze_progress(
            "1012650001",
            image_findings=site_findings,
            scheduled=scheduled,
        )
        exc = next(m for m in report.milestones if m.milestone_key == "EXCAVATION")
        assert exc.actual_pct == 100.0
        assert exc.verified is True
        assert report.overall_pct_complete > 0

    def test_drone_analytics_in_pipeline(self, site_findings):
        """Drone analytics processes volume data."""
        drone = DroneAnalyticsBridge()
        captures = [{"area_acres": 1.5, "altitude_ft": 200, "image_count": 150}]
        result = drone.analyze("1012650001", captures, site_findings)
        assert result.total_images == 150
        assert len(result.volumes) >= 1
        assert result.processing_time_sec <= 300.0 * 1.5

    def test_compliance_summary_after_audit(
        self, bridge, site_findings, dob_violations
    ):
        """After full audit, compliance summary is available."""
        bridge.run_full_pipeline(
            bbl="1012650001",
            images_processed=12,
            findings=site_findings,
            dob_violations=dob_violations,
            compliance_score=62.0,
            risk_score=78.0,
        )
        summary = bridge.get_site_compliance("1012650001")
        assert summary["status"] == "active"
        assert summary["proofs"] >= 1
        assert summary["total_images"] == 12
