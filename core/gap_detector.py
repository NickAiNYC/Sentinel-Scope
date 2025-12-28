"""
SentinelScope Gap Detector v2.0
Integrates NYC BC 2022 mapping, Fuzzy Matching, and Claude AI Reasoning.
"""

from typing import List, Optional
from fuzzywuzzy import fuzz, process
import anthropic
from core.models import GapAnalysisResponse, ComplianceGap
from core.constants import NYC_BC_REFS

class ComplianceGapEngine:
    TARGET_REQUIREMENTS = {
        "structural": {
            "Foundation": {"code": NYC_BC_REFS["STRUCTURAL"]["FOUNDATIONS"], "criticality": "Critical"},
            "Structural Steel": {"code": NYC_BC_REFS["STRUCTURAL"]["STEEL"], "criticality": "High"},
            "Fireproofing": {"code": NYC_BC_REFS["FIRE_PROTECTION"]["FIRE_RESISTANCE"], "criticality": "Critical"},
            "Decking": {"code": "BC Section 2210", "criticality": "Medium"},
            "Enclosure": {"code": "BC Chapter 14", "criticality": "Medium"}
        },
        "mep": {
            "MEP Rough-in": {"code": NYC_BC_REFS["MEP"]["MECHANICAL"], "criticality": "High"},
            "Fire Protection": {"code": "BC Chapter 9", "criticality": "Critical"},
            "Electrical Distribution": {"code": "NYC Electrical Code", "criticality": "High"},
            "HVAC Installation": {"code": "MC Chapter 6", "criticality": "Medium"}
        }
    }

    def __init__(self, project_type: str = "structural", fuzzy_threshold: int = 80):
        self.project_type = project_type.lower()
        self.fuzzy_threshold = fuzzy_threshold
        self.rules = self.TARGET_REQUIREMENTS.get(
            self.project_type, 
            self.TARGET_REQUIREMENTS["structural"]
        )

    def _get_ai_remediation(self, milestone: str, code: str, api_key: str) -> str:
        """Uses Claude to generate NYC-specific remediation steps."""
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"Expert NYC Construction Auditor: A project is missing evidence of '{milestone}' ({code}). Provide 2 concise remediation steps to satisfy NYC BC 2022."
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except:
            return f"Immediate site inspection for {milestone} required."

    def detect_gaps(self, found_milestones: List[str], api_key: Optional[str] = None) -> GapAnalysisResponse:
        missing_milestones = []
        
        for req, info in self.rules.items():
            # Enhanced Fuzzy Matching
            best_match = process.extractOne(req, found_milestones, scorer=fuzz.token_sort_ratio)
            is_present = best_match and best_match[1] >= self.fuzzy_threshold
            
            if not is_present:
                # Get AI Reasoning if API key is present
                remediation = self._get_ai_remediation(req, info['code'], api_key) if api_key else f"Submit evidence for {req}."
                
                missing_milestones.append(ComplianceGap(
                    milestone=req,
                    floor_range="TBD (Site-wide)",
                    dob_code=info["code"],
                    risk_level=info["criticality"],
                    deadline="Next Inspection Cycle",
                    recommendation=remediation
                ))

        # Stats calculation logic
        total_req = len(self.rules)
        gap_count = len(missing_milestones)
        found_count = total_req - gap_count
        coverage = (found_count / total_req) * 100 if total_req > 0 else 0
        
        priority = "Standard"
        if any(g.risk_level == "Critical" for g in missing_milestones):
            priority = "URGENT: Life Safety Compliance Required"

        return GapAnalysisResponse(
            missing_milestones=missing_milestones,
            compliance_score=int(coverage),
            risk_score=int(100 - coverage),
            total_found=found_count,
            gap_count=gap_count,
            next_priority=priority
        )
