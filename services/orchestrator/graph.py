"""
LangGraph Workflow Orchestration for SiteSentinel-AI

Integrates VisualScoutAgent into the multi-agent compliance pipeline.
Workflow: visual_scout → guard → fixer → proof
"""

from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import StateGraph, END

from ..agents.visual_scout import VisualScoutAgent
from ..agents.guard_agent import GuardAgent


# ============================================================================
# STATE SCHEMA
# ============================================================================

class AgentState(TypedDict, total=False):
    """
    LangGraph state schema for the compliance pipeline.
    
    Updated to include visual_findings from VisualScoutAgent.
    """
    # Input data
    site_id: Optional[str]
    org_id: Optional[str]
    image_url: Optional[str]  # NEW: Image for vision analysis
    
    # Visual Scout outputs
    visual_findings: Optional[str]
    milestones_detected: Optional[list[str]]
    violations_detected: Optional[list[str]]
    confidence_score: Optional[float]
    requires_legal_verification: Optional[bool]
    
    # Guard outputs
    guard_status: Optional[str]  # "pass" | "fail" | "warning"
    compliance_violations: Optional[list[str]]
    required_actions: Optional[list[str]]
    risk_level: Optional[str]
    
    # Fixer outputs (placeholder for future implementation)
    remediation_plan: Optional[str]
    fix_status: Optional[str]
    
    # Final proof
    proof_id: Optional[str]
    sha256_hash: Optional[str]
    
    # Agent tracking
    agent_source: Optional[str]
    error: Optional[str]


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def route_after_visual_scout(state: AgentState) -> str:
    """
    Route after VisualScoutAgent.
    
    If visual analysis succeeded → guard
    If error → end (graceful degradation)
    """
    if state.get("error"):
        return END
    return "guard"


def route_after_guard(state: AgentState) -> str:
    """
    Route after GuardAgent.
    
    If guard fails (critical violations) → end
    If guard passes → fixer
    If guard warning → fixer (with caution)
    """
    guard_status = state.get("guard_status", "pass")
    
    if guard_status == "fail":
        # Critical violations - stop pipeline
        return END
    
    # Pass or warning - continue to fixer
    return "fixer"


def fixer_placeholder(state: AgentState) -> AgentState:
    """
    Placeholder for FixerAgent.
    
    In the full implementation, this would:
    - Generate remediation plans for violations
    - Create work orders for contractors
    - Schedule follow-up inspections
    """
    required_actions = state.get("required_actions", [])
    
    if required_actions:
        remediation_plan = "\n".join([
            f"- {action}" for action in required_actions
        ])
    else:
        remediation_plan = "No remediation required - site is compliant"
    
    return {
        **state,
        "remediation_plan": remediation_plan,
        "fix_status": "planned",
        "agent_source": "Fixer"
    }


def proof_generator(state: AgentState) -> AgentState:
    """
    Generate SHA-256 proof for audit trail.
    
    In the full implementation, this would:
    - Hash all evidence (images + findings)
    - Store in blockchain or immutable ledger
    - Generate compliance certificate
    """
    import hashlib
    import json
    import uuid
    
    # Create proof payload
    proof_data = {
        "site_id": state.get("site_id"),
        "org_id": state.get("org_id"),
        "visual_findings": state.get("visual_findings"),
        "guard_status": state.get("guard_status"),
        "risk_level": state.get("risk_level"),
        "remediation_plan": state.get("remediation_plan")
    }
    
    # Generate SHA-256 hash
    proof_json = json.dumps(proof_data, sort_keys=True)
    sha256_hash = hashlib.sha256(proof_json.encode()).hexdigest()
    
    return {
        **state,
        "proof_id": str(uuid.uuid4()),
        "sha256_hash": sha256_hash,
        "agent_source": "ProofGenerator"
    }


# ============================================================================
# GRAPH BUILDER
# ============================================================================

def build_compliance_graph() -> StateGraph:
    """
    Build the LangGraph workflow for SiteSentinel-AI.
    
    Workflow:
        START → visual_scout → guard → fixer → proof → END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize agents
    visual_scout_agent = VisualScoutAgent()
    guard_agent = GuardAgent()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("visual_scout", visual_scout_agent.run)
    workflow.add_node("guard", guard_agent.run)
    workflow.add_node("fixer", fixer_placeholder)
    workflow.add_node("proof", proof_generator)
    
    # Define edges
    workflow.set_entry_point("visual_scout")
    
    workflow.add_conditional_edges(
        "visual_scout",
        route_after_visual_scout,
        {
            "guard": "guard",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "fixer": "fixer",
            END: END
        }
    )
    
    workflow.add_edge("fixer", "proof")
    workflow.add_edge("proof", END)
    
    # Compile
    return workflow.compile()


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def run_compliance_pipeline(
    site_id: str,
    org_id: str,
    image_url: str | None = None
) -> Dict[str, Any]:
    """
    Run the full compliance pipeline.
    
    Args:
        site_id: Site UUID
        org_id: Organization UUID
        image_url: Optional site image for vision analysis
    
    Returns:
        Final state with proof and compliance results
    """
    graph = build_compliance_graph()
    
    initial_state: AgentState = {
        "site_id": site_id,
        "org_id": org_id,
        "image_url": image_url
    }
    
    # Execute graph
    final_state = await graph.ainvoke(initial_state)
    
    return final_state
