"""Tests for VisionAgentBridge – ConComplyAi 5-agent integration."""

import pytest

from packages.vision_agent_bridge import (
    AgentMessage,
    AgentRole,
    DecisionProofRecord,
    SharedMemory,
    SiteAnalysis,
    TokenUsage,
    VisionAgentBridge,
    compute_decision_hash,
)

# ===== FIXTURES =====


@pytest.fixture
def bridge():
    """Create a fresh VisionAgentBridge."""
    return VisionAgentBridge()


@pytest.fixture
def sample_findings():
    return [
        {"name": "crack on wall", "confidence": 0.92, "type": "defect"},
        {"name": "missing guardrail", "confidence": 0.88, "type": "safety"},
    ]


@pytest.fixture
def sample_violations():
    return [
        {
            "violation_number": "V001",
            "violation_type": "Class B",
            "issue_date": "2026-01-15",
        },
    ]


# ===== MODEL TESTS =====


class TestSiteAnalysis:
    def test_creation(self):
        a = SiteAnalysis(bbl="1012650001")
        assert a.bbl == "1012650001"
        assert a.images_processed == 0
        assert a.compliance_score == 0.0

    def test_default_agent_source(self):
        a = SiteAnalysis(bbl="1012650001")
        assert a.agent_source == AgentRole.VISION


class TestTokenUsage:
    def test_record_image(self):
        t = TokenUsage()
        t.record_image(10)
        assert t.total_images == 10
        assert t.total_cost_usd == pytest.approx(0.001)

    def test_record_doc(self):
        t = TokenUsage()
        t.record_doc(5)
        assert t.total_docs == 5
        assert t.total_cost_usd == pytest.approx(0.0035)


class TestDecisionProofRecord:
    def test_immutable(self):
        from pydantic import ValidationError

        proof = DecisionProofRecord(
            bbl="1012650001",
            analysis_id="test-id",
            sha256_hash="abc123",
            compliance_score=80.0,
            risk_score=30.0,
        )
        with pytest.raises(ValidationError):
            proof.bbl = "changed"


# ===== SHARED MEMORY TESTS =====


class TestSharedMemory:
    def test_store_and_get_analysis(self):
        mem = SharedMemory()
        a = SiteAnalysis(bbl="100")
        mem.store_analysis(a)
        assert mem.get_analysis(a.analysis_id) is a

    def test_get_analyses_for_bbl(self):
        mem = SharedMemory()
        a1 = SiteAnalysis(bbl="100")
        a2 = SiteAnalysis(bbl="100")
        a3 = SiteAnalysis(bbl="200")
        mem.store_analysis(a1)
        mem.store_analysis(a2)
        mem.store_analysis(a3)
        assert len(mem.get_analyses_for_bbl("100")) == 2

    def test_send_and_get_messages(self):
        mem = SharedMemory()
        msg = AgentMessage(
            source_agent=AgentRole.VISION,
            target_agent=AgentRole.SYNTHESIS,
            payload={"key": "value"},
        )
        mem.send_message(msg)
        assert len(mem.get_messages_for(AgentRole.SYNTHESIS)) == 1
        assert len(mem.get_messages_for(AgentRole.RISK)) == 0

    def test_store_and_get_proofs(self):
        mem = SharedMemory()
        proof = DecisionProofRecord(
            bbl="100",
            analysis_id="a1",
            sha256_hash="hash",
            compliance_score=50.0,
            risk_score=40.0,
        )
        mem.store_proof(proof)
        assert len(mem.get_proofs_for_bbl("100")) == 1
        assert len(mem.get_proofs_for_bbl("999")) == 0


# ===== SHA-256 HASH TESTS =====


class TestDecisionHash:
    def test_deterministic(self):
        a = SiteAnalysis(
            bbl="100",
            images_processed=5,
            compliance_score=85.0,
            risk_score=20.0,
        )
        h1 = compute_decision_hash(a)
        h2 = compute_decision_hash(a)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    def test_different_data_different_hash(self):
        a1 = SiteAnalysis(bbl="100", compliance_score=80.0, risk_score=20.0)
        a2 = SiteAnalysis(bbl="200", compliance_score=80.0, risk_score=20.0)
        assert compute_decision_hash(a1) != compute_decision_hash(a2)


# ===== BRIDGE PIPELINE TESTS =====


class TestVisionAgentBridge:
    def test_submit_site_analysis(self, bridge, sample_findings):
        analysis = bridge.submit_site_analysis(
            bbl="100",
            images_processed=3,
            findings=sample_findings,
            compliance_score=75.0,
            risk_score=35.0,
        )
        assert analysis.bbl == "100"
        assert analysis.images_processed == 3
        assert len(analysis.findings) == 2
        # Check message was sent to Synthesis
        msgs = bridge.memory.get_messages_for(AgentRole.SYNTHESIS)
        assert len(msgs) == 1
        assert msgs[0].source_agent == AgentRole.VISION

    def test_relay_violations(self, bridge, sample_violations):
        msg = bridge.relay_violations("100", sample_violations)
        assert msg.source_agent == AgentRole.PERMIT
        assert msg.target_agent == AgentRole.SYNTHESIS
        assert bridge.memory.token_usage.total_docs == 1

    def test_synthesize_merges_violations(
        self, bridge, sample_findings, sample_violations
    ):
        analysis = bridge.submit_site_analysis(
            bbl="100", findings=sample_findings, compliance_score=70.0, risk_score=30.0,
        )
        bridge.relay_violations("100", sample_violations)
        result = bridge.synthesize(analysis.analysis_id)
        assert result is not None
        assert len(result.violations) == 1

    def test_synthesize_missing_analysis(self, bridge):
        assert bridge.synthesize("nonexistent") is None

    def test_red_team_validate(self, bridge, sample_findings):
        analysis = bridge.submit_site_analysis(
            bbl="100",
            findings=sample_findings,
            compliance_score=80.0,
            risk_score=25.0,
        )
        result = bridge.red_team_validate(analysis.analysis_id)
        assert result is not None
        for f in result.findings:
            assert f.get("red_team_validated") is True
            # Confidence should be reduced by 15%
            assert f["confidence"] < 1.0

    def test_red_team_missing_analysis(self, bridge):
        assert bridge.red_team_validate("nonexistent") is None

    def test_score_and_seal(self, bridge, sample_findings):
        analysis = bridge.submit_site_analysis(
            bbl="100",
            findings=sample_findings,
            compliance_score=80.0,
            risk_score=25.0,
        )
        proof = bridge.score_and_seal(analysis.analysis_id)
        assert proof is not None
        assert isinstance(proof, DecisionProofRecord)
        assert len(proof.sha256_hash) == 64
        assert proof.bbl == "100"
        assert proof.compliance_score == 80.0
        assert len(proof.agent_chain) == 5

    def test_score_and_seal_missing_analysis(self, bridge):
        assert bridge.score_and_seal("nonexistent") is None

    def test_run_full_pipeline(self, bridge, sample_findings, sample_violations):
        proof = bridge.run_full_pipeline(
            bbl="100",
            address="123 Test St",
            images_processed=5,
            findings=sample_findings,
            violations=[],
            dob_violations=sample_violations,
            compliance_score=85.0,
            risk_score=20.0,
        )
        assert proof is not None
        assert proof.bbl == "100"
        assert len(proof.sha256_hash) == 64
        assert proof.compliance_score == 85.0
        assert "5 images" in proof.summary

    def test_get_site_compliance_no_data(self, bridge):
        result = bridge.get_site_compliance("999")
        assert result["status"] == "no_data"

    def test_get_site_compliance_with_data(self, bridge, sample_findings):
        bridge.run_full_pipeline(
            bbl="100",
            images_processed=3,
            findings=sample_findings,
            compliance_score=90.0,
            risk_score=10.0,
        )
        result = bridge.get_site_compliance("100")
        assert result["status"] == "active"
        assert result["analyses"] == 1
        assert result["proofs"] == 1
        assert result["latest_compliance_score"] == 90.0

    def test_token_cost_tracking(self, bridge):
        bridge.run_full_pipeline(
            bbl="100",
            images_processed=10,
            compliance_score=50.0,
            risk_score=50.0,
        )
        assert bridge.memory.token_usage.total_images == 10
        assert bridge.memory.token_usage.total_cost_usd > 0
