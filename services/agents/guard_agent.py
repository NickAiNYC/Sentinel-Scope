"""
GuardAgent: NYC LL149/152 Compliance Verification

Validates findings from VisualScoutAgent against NYC Local Laws
and Building Code requirements. Acts as the legal gatekeeper.

Position in workflow: visual_scout → GUARD → fixer → proof
"""

import os
from typing import Any, Dict, List

from .base_agent import BaseAgent


class GuardAgent(BaseAgent):
    """
    The 'Legal Gatekeeper' of SiteSentinel-AI.
    
    Responsibilities:
    - Validate visual findings against NYC LL149 (Facade Inspection)
    - Validate against NYC LL152 (Gas Piping Inspection)
    - Cross-reference Building Code Chapter 33 violations
    - Determine if site can proceed to 'fixer' stage
    
    Prevents non-compliant sites from progressing without proper documentation.
    """
    
    # NYC Local Law 149: Facade Inspection
    LL149_REQUIREMENTS = {
        "facade_inspection": {
            "code": "NYC Admin Code §28-302",
            "frequency_years": 5,
            "applies_to": "Buildings > 6 stories"
        },
        "critical_examination": {
            "code": "NYC Admin Code §28-302.2",
            "required_for": "Unsafe conditions",
            "deadline_days": 30
        }
    }
    
    # NYC Local Law 152: Gas Piping Inspection  
    LL152_REQUIREMENTS = {
        "gas_piping_inspection": {
            "code": "NYC Admin Code §28-318",
            "frequency_years": 5,
            "applies_to": "Buildings with gas service"
        },
        "leak_survey": {
            "code": "NYC Admin Code §28-318.3",
            "required_for": "All accessible piping",
            "deadline_days": 30
        }
    }
    
    def __init__(self):
        """Initialize GuardAgent."""
        pass
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate visual findings against NYC compliance requirements.
        
        Args:
            state: LangGraph state containing:
                - visual_findings (Optional[str]): Analysis from VisualScout
                - violations_detected (Optional[List[str]]): BC Chapter 33 violations
                - milestones_detected (Optional[List[str]]): Progress milestones
                - requires_legal_verification (bool): Flag from VisualScout
        
        Returns:
            State update with:
                - guard_status (str): "pass" | "fail" | "warning"
                - compliance_violations (List[str]): LL149/152 violations
                - required_actions (List[str]): Remediation steps
                - risk_level (str): "Low" | "Medium" | "High" | "Critical"
        """
        # Check if legal verification is required
        requires_verification = state.get("requires_legal_verification", False)
        
        if not requires_verification:
            # VisualScout didn't run or skipped - pass through
            return {
                "guard_status": "pass",
                "agent_source": "Guard",
                "skipped_reason": "No legal verification required"
            }
        
        # Extract findings from VisualScout
        visual_findings = state.get("visual_findings")
        violations_detected = state.get("violations_detected", [])
        milestones_detected = state.get("milestones_detected", [])
        
        # Validate against NYC requirements
        compliance_violations = []
        required_actions = []
        
        # Check LL149 (Facade)
        ll149_violations, ll149_actions = self._check_ll149(
            visual_findings,
            violations_detected
        )
        compliance_violations.extend(ll149_violations)
        required_actions.extend(ll149_actions)
        
        # Check LL152 (Gas Piping)
        ll152_violations, ll152_actions = self._check_ll152(
            milestones_detected,
            violations_detected
        )
        compliance_violations.extend(ll152_violations)
        required_actions.extend(ll152_actions)
        
        # Check Chapter 33 violations
        ch33_violations, ch33_actions = self._check_chapter_33(
            violations_detected
        )
        compliance_violations.extend(ch33_violations)
        required_actions.extend(ch33_actions)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(compliance_violations)
        
        # Determine guard status
        if len(compliance_violations) == 0:
            guard_status = "pass"
        elif risk_level in ["Critical", "High"]:
            guard_status = "fail"
        else:
            guard_status = "warning"
        
        return {
            "guard_status": guard_status,
            "compliance_violations": compliance_violations,
            "required_actions": required_actions,
            "risk_level": risk_level,
            "agent_source": "Guard",
            "violations_count": len(compliance_violations)
        }
    
    def _check_ll149(
        self,
        visual_findings: str | None,
        violations: List[str]
    ) -> tuple[List[str], List[str]]:
        """Check LL149 (Facade Inspection) compliance."""
        found_violations = []
        actions = []
        
        if not visual_findings:
            return found_violations, actions
        
        # Check for facade-related violations
        findings_lower = visual_findings.lower()
        
        if "facade" in findings_lower and "unsafe" in findings_lower:
            found_violations.append(
                "LL149: Critical facade examination required (§28-302.2)"
            )
            actions.append(
                "Schedule QEWI (Qualified Exterior Wall Inspector) within 30 days"
            )
        
        return found_violations, actions
    
    def _check_ll152(
        self,
        milestones: List[str],
        violations: List[str]
    ) -> tuple[List[str], List[str]]:
        """Check LL152 (Gas Piping) compliance."""
        found_violations = []
        actions = []
        
        # Check if gas work is present
        has_gas_work = any(
            "gas" in str(m).lower() or "piping" in str(m).lower()
            for m in milestones
        )
        
        if has_gas_work:
            actions.append(
                "LL152: Verify licensed master plumber GPS-1 filing (§28-318)"
            )
        
        return found_violations, actions
    
    def _check_chapter_33(
        self,
        violations: List[str]
    ) -> tuple[List[str], List[str]]:
        """Check Building Code Chapter 33 violations."""
        found_violations = []
        actions = []
        
        # Critical violations that must be addressed immediately
        critical_patterns = {
            "§3314": "Fall protection violation - STOP WORK",
            "§3314.9": "Scaffold safety violation - STOP WORK",
            "§3308": "Fire safety violation - Immediate remediation required"
        }
        
        for violation in violations:
            for pattern, action in critical_patterns.items():
                if pattern in violation:
                    found_violations.append(violation)
                    actions.append(action)
        
        return found_violations, actions
    
    def _calculate_risk_level(self, violations: List[str]) -> str:
        """Calculate overall risk level."""
        if not violations:
            return "Low"
        
        # Check for STOP WORK violations
        stop_work_count = sum(
            1 for v in violations
            if "STOP WORK" in v or "Critical" in v
        )
        
        if stop_work_count > 0:
            return "Critical"
        elif len(violations) >= 3:
            return "High"
        elif len(violations) >= 1:
            return "Medium"
        else:
            return "Low"
