"""
SentinelScope Gap Detector v2.0
Integrates NYC BC 2022 mapping, Fuzzy Matching, and Claude AI Reasoning.
"""

from typing import List, Optional
from fuzzywuzzy import fuzz, process
import anthropic
from core.models import GapAnalysisResponse, ComplianceGap, CaptureClassification
from core.constants import NYC_BC_REFS

class ComplianceGapEngine:
    TARGET_REQUIREMENTS = {
        "structural": {
            "Foundation": {"code": NYC_BC_REFS["STRUCTURAL"]["FOUNDATIONS"], "criticality": "Critical", "weight": 40},
            "Structural Steel": {"code": NYC_BC_REFS["STRUCTURAL"]["STEEL"], "criticality": "High", "weight": 25},
            "Fireproofing": {"code": NYC_BC_REFS["FIRE_PROTECTION"]["FIRE_RESISTANCE"], "criticality": "Critical", "weight": 20},
            "Decking": {"code": "BC Section 2210", "criticality": "Medium", "weight": 10},
            "Enclosure": {"code": "BC Chapter 14", "criticality": "Medium", "weight": 5}
        },
        "mep": {
            "MEP Rough-in": {"code": NYC_BC_REFS["MEP"]["MECHANICAL"], "criticality": "High", "weight": 30},
            "Fire Protection": {"code": "BC Chapter 9", "criticality": "Critical", "weight": 40},
            "Electrical Distribution": {"code": "NYC Electrical Code", "criticality": "High", "weight": 20},
            "HVAC Installation": {"code": "MC Chapter 6", "criticality": "Medium", "weight": 10}
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
        prompt = (f"Expert NYC Construction Auditor: A project is missing evidence of '{milestone}' ({code}). "
                  f"Provide 2 concise remediation steps to satisfy NYC BC 2022.")
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except:
            return f"Immediate site inspection for {milestone} required to verify {code}."

    def detect_gaps(self, findings: List[CaptureClassification], api_key: Optional[str] = None) -> GapAnalysisResponse:
        """
        Analyzes findings against NYC BC 2022 requirements.
        findings: List of CaptureClassification objects from the AI Processor.
        """
        # Extract milestone strings from the CaptureClassification objects
        found_names = [f.milestone for f in findings if f.confidence > 0.4]
        
        missing_milestones = []
        earned_weight = 0
        total_weight = sum(info['weight'] for info in self.rules.values())

        for req, info in self.rules.items():
            # Enhanced Fuzzy Matching to catch variations in AI naming
            best_match = process.extractOne(req, found_names, scorer=fuzz.token_sort_ratio)
            is_present = best_match and best_match[1] >= self.fuzzy_threshold
            
            if is_present:
                earned_weight += info['weight']
            else:
                # Assign DOB Class based on criticality
                dob_class_map = {"Critical": "Class C", "High": "Class B", "Medium": "Class B", "Low": "Class A"}
                current_class = dob_class_map.get(info["criticality"], "Class B")

                # Get AI Remediation if API key is present
                remediation = self._get_ai_remediation(req, info['code'], api_key) if api_key else f"Submit field evidence for {req}."
                
                missing_milestones.append(ComplianceGap(
                    milestone=req,
                    floor_range="TBD (Audit Pending)",
                    dob_code=info["code"],
                    risk_level=info["criticality"],
                    dob_class=current_class,
                    deadline="Within 48 Hours" if info["criticality"] == "Critical" else "Next Inspection",
                    recommendation=remediation
                ))

        # Calculate weighted scores
        compliance_score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
        risk_score = 100 - compliance_score
        
        # Priority Message
        priority = "✅ Project On Track"
        critical_gaps = [g for g in missing_milestones if g.risk_level == "Critical"]
        if critical_gaps:
            priority = f"🚨 URGENT: {len(critical_gaps)} Critical Life Safety Gaps Found"
        elif compliance_score < 70:
            priority = "⚠️ ACTION REQUIRED: Significant Compliance Gaps"

        return GapAnalysisResponse(
            missing_milestones=missing_milestones,
            compliance_score=compliance_score,
            risk_score=risk_score,
            total_found=len(found_names),
            gap_count=len(missing_milestones),
            next_priority=priority
        )
