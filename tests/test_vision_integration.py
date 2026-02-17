"""
Test Suite for Scope Vision Integration

Tests the VisualScoutAgent, GuardAgent, and LangGraph orchestration.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agents.visual_scout import VisualScoutAgent
from services.agents.guard_agent import GuardAgent
from services.orchestrator.graph import (
    build_compliance_graph,
    run_compliance_pipeline,
    AgentState
)


# ============================================================================
# VISUAL SCOUT TESTS
# ============================================================================

class TestVisualScoutAgent:
    """Test VisualScoutAgent functionality."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-123")
    
    def test_init_requires_api_key(self):
        """Test that VisualScoutAgent requires DEEPSEEK_API_KEY."""
        import os
        
        # Remove API key if present
        old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        
        try:
            with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
                VisualScoutAgent()
        finally:
            # Restore key
            if old_key:
                os.environ["DEEPSEEK_API_KEY"] = old_key
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_no_image(self, mock_env):
        """Test that agent handles missing image gracefully."""
        agent = VisualScoutAgent()
        
        result = await agent.run({
            "site_id": "test-site",
            "org_id": "test-org"
            # No image_url provided
        })
        
        assert result["visual_findings"] is None
        assert result["agent_source"] == "VisualScout"
        assert result["skipped_reason"] == "No site imagery provided"
        assert result["requires_legal_verification"] is False
    
    @pytest.mark.asyncio
    async def test_vision_analysis_success(self, mock_env):
        """Test successful vision analysis."""
        agent = VisualScoutAgent()
        
        # Mock DeepSeek API response
        mock_response = {
            "choices": [{
                "message": {
                    "content": """MILESTONE: Foundation
FLOOR: 1
SAFETY_STATUS: Compliant
VIOLATIONS: None
CONFIDENCE: 0.9
NOTES: Clear foundation work visible"""
                }
            }]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            result = await agent.run({
                "site_id": "test-site",
                "org_id": "test-org",
                "image_url": "https://example.com/test.jpg"
            })
            
            assert "visual_findings" in result
            assert result["agent_source"] == "VisualScout"
            assert result["requires_legal_verification"] is True
            assert result["confidence_score"] == 0.9
            assert "Foundation" in result["milestones_detected"]
    
    @pytest.mark.asyncio
    async def test_vision_api_timeout(self, mock_env):
        """Test handling of API timeout."""
        import httpx
        
        agent = VisualScoutAgent()
        
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
            result = await agent.run({
                "site_id": "test-site",
                "org_id": "test-org",
                "image_url": "https://example.com/test.jpg"
            })
            
            assert result["error"] == "timeout"
            assert "timeout" in result["visual_findings"].lower()


# ============================================================================
# GUARD AGENT TESTS
# ============================================================================

class TestGuardAgent:
    """Test GuardAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_guard_skips_without_verification(self):
        """Test that guard skips when no verification needed."""
        agent = GuardAgent()
        
        result = await agent.run({
            "requires_legal_verification": False
        })
        
        assert result["guard_status"] == "pass"
        assert result["skipped_reason"] == "No legal verification required"
    
    @pytest.mark.asyncio
    async def test_guard_detects_critical_violations(self):
        """Test that guard detects critical violations."""
        agent = GuardAgent()
        
        result = await agent.run({
            "requires_legal_verification": True,
            "visual_findings": "Safety issues detected",
            "violations_detected": ["BC §3314: Fall protection missing - STOP WORK"]
        })
        
        assert result["guard_status"] == "fail"
        assert result["risk_level"] == "Critical"
        assert len(result["compliance_violations"]) > 0
    
    @pytest.mark.asyncio
    async def test_guard_passes_compliant_site(self):
        """Test that guard passes compliant site."""
        agent = GuardAgent()
        
        result = await agent.run({
            "requires_legal_verification": True,
            "visual_findings": "Site is compliant",
            "violations_detected": [],
            "milestones_detected": ["Foundation", "Structural Steel", "Fireproofing"]
        })
        
        assert result["guard_status"] == "pass"
        assert result["risk_level"] == "Low"


# ============================================================================
# LANGGRAPH ORCHESTRATION TESTS
# ============================================================================

class TestLangGraphOrchestration:
    """Test LangGraph workflow orchestration."""
    
    @pytest.mark.asyncio
    async def test_pipeline_with_image(self, monkeypatch):
        """Test full pipeline with image."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        
        # Mock vision API
        mock_vision_response = {
            "choices": [{
                "message": {
                    "content": """MILESTONE: Foundation
VIOLATIONS: None
CONFIDENCE: 0.85"""
                }
            }]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_vision_response
            mock_post.return_value.raise_for_status = Mock()
            
            result = await run_compliance_pipeline(
                site_id="test-site",
                org_id="test-org",
                image_url="https://example.com/test.jpg"
            )
            
            # Check that pipeline completed
            assert "proof_id" in result
            assert "sha256_hash" in result
            assert result["agent_source"] == "ProofGenerator"
    
    @pytest.mark.asyncio
    async def test_pipeline_without_image(self, monkeypatch):
        """Test pipeline gracefully handles missing image."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        
        result = await run_compliance_pipeline(
            site_id="test-site",
            org_id="test-org",
            image_url=None  # No image
        )
        
        # Pipeline should still complete
        assert result is not None
        # Visual scout should have been skipped
        assert result.get("visual_findings") is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_compliant_site(self, monkeypatch):
        """Test complete workflow for compliant site."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": """MILESTONE: Foundation
FLOOR: 1
SAFETY_STATUS: Compliant
VIOLATIONS: None
CONFIDENCE: 0.95
NOTES: All safety measures in place"""
                }
            }]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            result = await run_compliance_pipeline(
                site_id="test-site-123",
                org_id="org-456",
                image_url="https://example.com/compliant-site.jpg"
            )
            
            # Verify complete pipeline execution
            assert result["visual_findings"] is not None
            assert result["guard_status"] in ["pass", "warning"]
            assert result["remediation_plan"] is not None
            assert result["proof_id"] is not None
            assert result["sha256_hash"] is not None
            assert len(result["sha256_hash"]) == 64  # SHA-256 hex length
    
    @pytest.mark.asyncio
    async def test_full_workflow_violation_site(self, monkeypatch):
        """Test complete workflow for site with violations."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": """MILESTONE: Superstructure
FLOOR: 5
SAFETY_STATUS: Violation
VIOLATIONS: BC §3314.1: Missing fall protection
CONFIDENCE: 0.88
NOTES: Workers visible without proper fall arrest systems"""
                }
            }]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            result = await run_compliance_pipeline(
                site_id="test-site-456",
                org_id="org-789",
                image_url="https://example.com/violation-site.jpg"
            )
            
            # Verify violation detection
            assert "fall protection" in result["visual_findings"].lower()
            assert result["guard_status"] == "fail"
            assert result["risk_level"] == "Critical"
            assert len(result["required_actions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
