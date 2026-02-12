"""Tests for LL149, LL152, and LL11 local law bridges."""

import pytest

from packages.ll11_facade_vision_bridge import (
    FacadeCondition,
    LL11FacadeVisionBridge,
)
from packages.ll149_inspector_bridge import (
    LL149InspectorBridge,
    SuperintendentStatus,
)
from packages.ll152_gas_tracker_bridge import (
    GasPipingStatus,
    LL152GasTrackerBridge,
)

# ===== LL149 TESTS =====


class TestLL149InspectorBridge:
    @pytest.fixture
    def bridge(self):
        return LL149InspectorBridge()

    def test_superintendent_present(self, bridge):
        findings = [
            {
                "name": "Superintendent Smith",
                "entity_type": "Worker",
                "confidence": 0.95,
            },
        ]
        result = bridge.analyze_site("100", findings, permit_type="NB")
        assert result.superintendent_status == SuperintendentStatus.PRESENT
        assert result.violation_probability < 0.10

    def test_superintendent_not_detected_nb_permit(self, bridge):
        findings = [
            {"name": "Worker-123", "entity_type": "Worker", "confidence": 0.90},
        ]
        result = bridge.analyze_site(
            "100", findings, permit_type="NB"
        )
        assert result.superintendent_status == SuperintendentStatus.NOT_DETECTED
        assert result.violation_probability >= 0.87

    def test_insufficient_evidence(self, bridge):
        result = bridge.analyze_site(
            "100", image_findings=[], permit_type="NB"
        )
        assert result.superintendent_status == (
            SuperintendentStatus.INSUFFICIENT_EVIDENCE
        )

    def test_no_permit_lower_probability(self, bridge):
        findings = [
            {
                "name": "Worker-001",
                "entity_type": "Worker",
                "confidence": 0.90,
            },
        ]
        result = bridge.analyze_site("100", findings, permit_type="A3")
        assert result.violation_probability < 0.87  # lower than NB

    def test_ssm_keyword_detected(self, bridge):
        findings = [
            {
                "name": "SSM Badge #42",
                "entity_type": "site safety manager",
                "confidence": 0.88,
            },
        ]
        result = bridge.analyze_site("100", findings, permit_type="DM")
        assert result.superintendent_status == SuperintendentStatus.PRESENT

    def test_get_findings_filtered(self, bridge):
        bridge.analyze_site("100", [])
        bridge.analyze_site("200", [])
        assert len(bridge.get_findings("100")) == 1
        assert len(bridge.get_findings()) == 2


# ===== LL152 TESTS =====


class TestLL152GasTrackerBridge:
    @pytest.fixture
    def bridge(self):
        return LL152GasTrackerBridge()

    def test_gas_piping_with_sticker(self, bridge):
        findings = [
            {
                "name": "gas pipe riser",
                "evidence_notes": "inspection sticker visible",
                "confidence": 0.92,
            },
        ]
        result = bridge.analyze_site("100", findings)
        assert result.gas_piping_status == GasPipingStatus.COMPLIANT
        assert result.inspection_sticker_detected is True
        assert result.violation_probability <= 0.05

    def test_gas_piping_no_sticker(self, bridge):
        findings = [
            {"name": "gas piping installation", "confidence": 0.90},
        ]
        result = bridge.analyze_site("100", findings)
        assert result.gas_piping_status == GasPipingStatus.PIPING_DETECTED_NO_STICKER
        assert result.violation_probability >= 0.88
        assert "GPS-1" in result.gps_form_reminder

    def test_no_gas_piping(self, bridge):
        findings = [
            {"name": "electrical panel", "confidence": 0.85},
        ]
        result = bridge.analyze_site("100", findings)
        assert result.gas_piping_status == GasPipingStatus.NO_GAS_PIPING
        assert result.violation_probability == 0.0

    def test_insufficient_evidence(self, bridge):
        result = bridge.analyze_site("100")
        assert result.gas_piping_status == GasPipingStatus.INSUFFICIENT_EVIDENCE

    def test_get_findings_filtered(self, bridge):
        bridge.analyze_site("100", [])
        bridge.analyze_site("200", [])
        assert len(bridge.get_findings("100")) == 1


# ===== LL11 TESTS =====


class TestLL11FacadeVisionBridge:
    @pytest.fixture
    def bridge(self):
        return LL11FacadeVisionBridge()

    def test_crack_detection_unsafe(self, bridge):
        findings = [
            {"name": "facade crack >1/4 inch", "confidence": 0.94},
        ]
        result = bridge.analyze_facade("100", findings)
        assert result.facade_condition == FacadeCondition.UNSAFE
        assert result.violation_probability >= 0.85
        assert result.critical_exam_required is True

    def test_spalling_safe_with_repair(self, bridge):
        findings = [
            {"name": "spalling on facade", "confidence": 0.88},
        ]
        result = bridge.analyze_facade("100", findings)
        assert result.facade_condition == FacadeCondition.SAFE_WITH_REPAIR
        assert "spalling" in result.defects_detected

    def test_pre_1950_multiplier(self, bridge):
        findings = [
            {"name": "water damage staining", "confidence": 0.80},
        ]
        result_old = bridge.analyze_facade("100", findings, year_built=1940)
        result_new = bridge.analyze_facade("200", findings, year_built=2010)
        assert result_old.pre_1950_multiplier == 2.8
        assert result_new.pre_1950_multiplier == 1.0
        assert result_old.violation_probability > result_new.violation_probability

    def test_safe_facade(self, bridge):
        findings = [
            {"name": "clean facade", "confidence": 0.95},
        ]
        result = bridge.analyze_facade("100", findings)
        assert result.facade_condition == FacadeCondition.SAFE
        assert result.violation_probability <= 0.05
        assert result.critical_exam_required is False

    def test_insufficient_evidence(self, bridge):
        result = bridge.analyze_facade("100")
        assert result.facade_condition == FacadeCondition.INSUFFICIENT_EVIDENCE

    def test_multiple_defects_unsafe(self, bridge):
        findings = [
            {"name": "crack", "confidence": 0.90},
            {"name": "spalling", "confidence": 0.85},
            {"name": "corrosion", "confidence": 0.80},
        ]
        result = bridge.analyze_facade("100", findings)
        assert result.facade_condition == FacadeCondition.UNSAFE
        assert len(result.defects_detected) >= 3

    def test_critical_exam_note_in_evidence(self, bridge):
        findings = [{"name": "facade crack", "confidence": 0.90}]
        result = bridge.analyze_facade("100", findings)
        assert "Critical Examination Report" in result.evidence_notes

    def test_get_findings_filtered(self, bridge):
        bridge.analyze_facade("100", [])
        bridge.analyze_facade("200", [])
        assert len(bridge.get_findings("100")) == 1
