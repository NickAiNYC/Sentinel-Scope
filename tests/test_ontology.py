"""Tests for ontology modules – state machines, enforcement, milestones."""

import pytest

from ontology.violation_states import ViolationState, ViolationStateMachine
from ontology.permit_lifecycle import PermitStage, PermitLifecycle
from ontology.enforcement import EscalationGraph, EscalationLevel, EnforcementCategory
from ontology.milestones import MilestonePhase, MilestoneTaxonomy


# ===== VIOLATION STATE MACHINE =====


class TestViolationStateMachine:
    def test_valid_transition(self):
        """REPORTED → ACKNOWLEDGED should be valid."""
        assert ViolationStateMachine.can_transition(
            ViolationState.REPORTED, ViolationState.ACKNOWLEDGED
        ) is True

    def test_invalid_transition(self):
        """REPORTED → RESOLVED should be invalid (skips required steps)."""
        assert ViolationStateMachine.can_transition(
            ViolationState.REPORTED, ViolationState.RESOLVED
        ) is False

    def test_get_next_states(self):
        """REPORTED should have ACKNOWLEDGED and DISMISSED as next states."""
        next_states = ViolationStateMachine.get_next_states(ViolationState.REPORTED)
        assert ViolationState.ACKNOWLEDGED in next_states
        assert ViolationState.DISMISSED in next_states
        assert len(next_states) == 2


# ===== PERMIT LIFECYCLE =====


class TestPermitLifecycle:
    def test_valid_transition(self):
        """APPLIED → UNDER_REVIEW should be valid."""
        assert PermitLifecycle.can_transition(
            PermitStage.APPLIED, PermitStage.UNDER_REVIEW
        ) is True

    def test_invalid_transition(self):
        """APPLIED → ACTIVE should be invalid (skips approval)."""
        assert PermitLifecycle.can_transition(
            PermitStage.APPLIED, PermitStage.ACTIVE
        ) is False


# ===== ESCALATION GRAPH =====


class TestEscalationGraph:
    def test_low_risk_notice(self):
        """Risk score 10 should give NOTICE level."""
        level = EscalationGraph.get_escalation_level(10)
        assert level == EscalationLevel.NOTICE

    def test_high_risk_order(self):
        """Risk score 75 should give ORDER level."""
        level = EscalationGraph.get_escalation_level(75)
        assert level == EscalationLevel.ORDER

    def test_enforcement_actions(self):
        """Emergency level should include STOP_WORK_ORDER."""
        actions = EscalationGraph.get_likely_enforcement(90, "default")
        action_values = [str(a) for a in actions]
        assert "stop_work_order" in action_values


# ===== MILESTONE TAXONOMY =====


class TestMilestoneTaxonomy:
    def test_get_phase_milestones(self):
        """FOUNDATION phase should have known milestones."""
        milestones = MilestoneTaxonomy.get_phase_milestones(MilestonePhase.FOUNDATION)
        assert len(milestones) > 0
        assert "Excavation completed" in milestones

    def test_get_phase_for_milestone(self):
        """'Excavation completed' should map back to FOUNDATION phase."""
        phase = MilestoneTaxonomy.get_phase_for_milestone("Excavation completed")
        assert phase == MilestonePhase.FOUNDATION
