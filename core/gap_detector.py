"""
SentinelScope Gap Detector v2.5 (2025.12 Update)
Integrates NYC BC 2022/2025 mapping, RapidFuzz Matching, and Claude 4.5 Reasoning.
"""

from typing import List, Optional

import anthropic
from rapidfuzz import fuzz, process

from core.constants import NYC_BC_REFS
from core.models import CaptureClassification, ComplianceGap, GapAnalysisResponse


class ComplianceGapEngine:
    # 2025 Enhanced Domain Logic
    TARGET_REQUIREMENTS = {
        "structural": {
            "Foundation": {"code": NYC_BC_REFS["STRUCTURAL"]["FOUNDATIONS"], "criticality": "Critical", "weight": 35},
            "Structural Steel": {"code": NYC_BC_REFS["STRUCTURAL"]["STEEL"], "criticality": "High", "weight": 25},
            "Fireproofing": {"code": NYC_BC_REFS["FIRE_PROTECTION"]["FIRE_RESISTANCE"], "criticality": "Critical", "weight": 20},
            "Cold-Formed Steel": {"code": "BC Section 2210", "criticality": "Medium", "weight": 10},
            "Exterior Walls": {"code": "BC Chapter 14", "criticality": "Medium", "weight": 10}
        },
        "mep": {
            "MEP Rough-in": {"code": NYC_BC_REFS["MEP"]["MECHANICAL"], "criticality": "High", "weight": 25},
            "Fire Protection": {"code": "BC Chapter 9", "criticality": "Critical", "weight": 35},
            "Electrical Distribution": {"code": "NYC Electrical Code (2025)", "criticality": "High", "weight": 25},
            "HVAC Installation": {"code": "MC Chapter 6", "criticality": "Medium", "weight": 15}
        }
    }

    def __init__(self, project_type: str = "structural", fuzzy_threshold: int = 85):
        self.project_type = project_type.lower()
        self.fuzzy_threshold = fuzzy_threshold
        self.rules = self.TARGET_REQUIREMENTS.get(
            self.project_type, 
            self.TARGET_REQUIREMENTS["structural"]
        )

    def _get_ai_remediation(self, milestone: str, code: str, api_key: str) -> str:
        """Uses Claude 4.5 Opus for SOTA NYC-specific remediation steps."""
        client = anthropic.Anthropic(api_key=api_key)
        # 2025 System Prompt: Higher instruction following for legal/code compliance
        prompt = (f"Act as a Senior NYC DOB Auditor. A project site is missing evidence of '{milestone}' "
                  f"under {code}. Based on NYC BC 2022 and 2025 updates, provide 2 precise, "
                  f"field-actionable remediation steps to clear this gap. Be concise.")
        try:
            message = client.messages.create(
                model="claude-4-5-opus-20251101",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception:
            return f"🚨 URGENT: Conduct physical site audit for {milestone}. Verify compliance with {code} immediately."

    def detect_gaps(self, findings: list[CaptureClassification], api_key: str | None = None) -> GapAnalysisResponse:
        """Analyzes AI findings against NYC regulatory requirements."""
        # Use a higher confidence floor for forensic data to reduce false positives
        found_names = [f.milestone for f in findings if f.confidence > 0.6]
        
        missing_milestones = []
        earned_weight = 0
        total_weight = sum(info['weight'] for info in self.rules.values())

        for req, info in self.rules.items():
            # RapidFuzz: 2025 standard for high-speed string matching
            match_result = process.extractOne(req, found_names, scorer=fuzz.WRatio)
            is_present = match_result and match_result[1] >= self.fuzzy_threshold
            
            if is_present:
                earned_weight += info['weight']
            else:
                # Severity Mapping for NYC DOB Classes
                severity_to_class = {"Critical": "Class C", "High": "Class B", "Medium": "Class B", "Low": "Class A"}
                current_class = severity_to_class.get(info["criticality"], "Class B")

                # Context-Aware Remediation
                remediation = self._get_ai_remediation(req, info['code'], api_key) if api_key else f"Request photo evidence for {req}."
                
                missing_milestones.append(ComplianceGap(
                    milestone=req,
                    floor_range="Audit Required",
                    dob_code=info["code"],
                    risk_level=info["criticality"],
                    dob_class=current_class,
                    deadline="Immediately" if info["criticality"] == "Critical" else "Within 7 Days",
                    recommendation=remediation
                ))

        # Scoring Logic (Weighted Compliance)
        compliance_score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
        risk_score = 100 - compliance_score
        
        # Summary messaging for the Streamlit Sidebar
        critical_count = sum(1 for g in missing_milestones if g.risk_level == "Critical")
        if critical_count > 0:
            priority = f"🚨 {critical_count} CRITICAL GAPS: STOP WORK RISK"
        elif compliance_score < 75:
            priority = "⚠️ CAUTION: Significant Evidence Gaps"
        else:
            priority = "✅ COMPLIANT: Standard Monitoring"

        return GapAnalysisResponse(
            missing_milestones=missing_milestones,
            compliance_score=compliance_score,
            risk_score=risk_score,
            total_found=len(found_names),
            gap_count=len(missing_milestones),
            next_priority=priority
        )
