"""Tests for OSHA 1926 Safety Violation Detector."""

import pytest

from core.safety_violation_detector import (
    SafetyViolationDetector,
    ViolationType,
)


@pytest.fixture
def detector():
    return SafetyViolationDetector()


class TestSafetyViolationDetector:
    def test_no_findings_returns_low_risk(self, detector):
        result = detector.analyze("100")
        assert result.overall_risk == "LOW"
        assert result.total_violations == 0

    def test_fall_protection_detection(self, detector):
        findings = [
            {"name": "no fall protection on 3rd floor", "confidence": 0.95},
        ]
        result = detector.analyze("100", findings)
        assert result.total_violations == 1
        v = result.violations[0]
        assert v.violation_type == ViolationType.FALL_PROTECTION
        assert v.osha_standard == "1926.501"
        assert v.stop_work_required is True

    def test_ppe_noncompliance_detection(self, detector):
        findings = [
            {"name": "worker no hard hat", "confidence": 0.88},
        ]
        result = detector.analyze("100", findings)
        assert result.total_violations == 1
        assert result.violations[0].violation_type == ViolationType.PPE_NONCOMPLIANCE

    def test_scaffolding_violation(self, detector):
        findings = [
            {
                "name": "unsafe scaffold",
                "evidence_notes": "missing plank",
                "confidence": 0.90,
            },
        ]
        result = detector.analyze("100", findings)
        assert any(
            v.violation_type == ViolationType.SCAFFOLDING
            for v in result.violations
        )

    def test_excavation_violation(self, detector):
        findings = [
            {"name": "unshored excavation", "confidence": 0.93},
        ]
        result = detector.analyze("100", findings)
        assert any(
            v.violation_type == ViolationType.EXCAVATION
            for v in result.violations
        )

    def test_electrical_violation(self, detector):
        findings = [
            {"name": "exposed wiring near water", "confidence": 0.85},
        ]
        result = detector.analyze("100", findings)
        assert any(
            v.violation_type == ViolationType.ELECTRICAL
            for v in result.violations
        )

    def test_ladder_violation(self, detector):
        findings = [
            {"name": "damaged ladder on site", "confidence": 0.78},
        ]
        result = detector.analyze("100", findings)
        assert any(v.violation_type == ViolationType.LADDER for v in result.violations)

    def test_housekeeping_violation(self, detector):
        findings = [
            {
                "name": "debris blocking exit",
                "evidence_notes": "tripping hazard",
                "confidence": 0.80,
            },
        ]
        result = detector.analyze("100", findings)
        assert any(
            v.violation_type == ViolationType.HOUSEKEEPING
            for v in result.violations
        )

    def test_fire_protection_violation(self, detector):
        findings = [
            {"name": "no fire extinguisher on floor 2", "confidence": 0.87},
        ]
        result = detector.analyze("100", findings)
        assert any(
            v.violation_type == ViolationType.FIRE_PROTECTION
            for v in result.violations
        )

    def test_multiple_violations_high_risk(self, detector):
        findings = [
            {"name": "worker no hard hat", "confidence": 0.88},
            {"name": "debris tripping hazard", "confidence": 0.80},
            {"name": "damaged ladder", "confidence": 0.75},
        ]
        result = detector.analyze("100", findings)
        assert result.total_violations == 3
        assert result.overall_risk == "HIGH"

    def test_stop_work_critical_risk(self, detector):
        findings = [
            {"name": "no fall protection", "confidence": 0.95},
        ]
        result = detector.analyze("100", findings)
        assert result.overall_risk == "CRITICAL"
        assert result.stop_work_violations == 1

    def test_all_8_violation_types(self, detector):
        """Verify all 8 OSHA violation types can be detected."""
        findings = [
            {"name": "no fall protection", "confidence": 0.9},
            {"name": "no hard hat", "confidence": 0.9},
            {"name": "unsafe scaffold", "confidence": 0.9},
            {"name": "unshored excavation", "confidence": 0.9},
            {"name": "exposed wiring", "confidence": 0.9},
            {"name": "damaged ladder", "confidence": 0.9},
            {"name": "debris tripping hazard", "confidence": 0.9},
            {"name": "no fire extinguisher", "confidence": 0.9},
        ]
        result = detector.analyze("100", findings)
        assert result.total_violations == 8
        detected_types = {v.violation_type for v in result.violations}
        assert detected_types == {
            ViolationType.FALL_PROTECTION,
            ViolationType.PPE_NONCOMPLIANCE,
            ViolationType.SCAFFOLDING,
            ViolationType.EXCAVATION,
            ViolationType.ELECTRICAL,
            ViolationType.LADDER,
            ViolationType.HOUSEKEEPING,
            ViolationType.FIRE_PROTECTION,
        }

    def test_get_results_filtered(self, detector):
        detector.analyze("100", [{"name": "no hard hat", "confidence": 0.9}])
        detector.analyze("200", [])
        assert len(detector.get_results("100")) == 1
        assert len(detector.get_results()) == 2
