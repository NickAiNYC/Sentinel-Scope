"""
SentinelScope Gap Detector
Analyzes classified milestones against NYC Building Code 2022 requirements.
Returns validated Pydantic models for the Sentinel Dashboard.
"""

from typing import List
from core.models import GapAnalysisResponse, ComplianceGap
from core.constants import NYC_BC_REFS

class ComplianceGapEngine:
    # Industry-standard requirements mapped to NYC Building Code 2022
    # These are our 'Target State' milestones
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

    def __init__(self, project_type: str = "structural"):
        self.project_type = project_type.lower()
        self.rules = self.TARGET_REQUIREMENTS.get(
            self.project_type, 
            self.TARGET_REQUIREMENTS["structural"]
        )

    def detect_gaps(self, found_milestones: List[str]) -> GapAnalysisResponse:
        """
        Compares found evidence against NYC requirements.
        Returns a validated GapAnalysisResponse object.
        """
        found_normalized = [m.lower() for m in found_milestones]
        missing_milestones = []
        
        for req, info in self.rules.items():
            # Check for matches (e.g., "Fireproofing Spray" matches "Fireproofing")
            is_present = any(req.lower() in f_norm or f_norm in req.lower() for f_norm in found_normalized)
            
            if not is_present:
                missing_milestones.append(ComplianceGap(
                    milestone=req,
                    floor_range="TBD (Site-wide)",
                    dob_code=info["code"],
                    risk_level=info["criticality"],
                    deadline="Next Inspection Cycle",
                    recommendation=f"Submit evidence of {req} to satisfy {info['code']}."
                ))

        # Calculate Statistics
        total_req = len(self.rules)
        gap_count = len(missing_milestones)
        found_count = total_req - gap_count
        coverage = (found_count / total_req) * 100 if total_req > 0 else 0
        
        # Determine Priority based on criticality of gaps
        priority = "Standard Maintenance"
        if any(g.risk_level == "Critical" for g in missing_milestones):
            priority = "URGENT: Life Safety Compliance Required"
        elif gap_count > 0:
            priority = "Address Missing Documentation"

        # Return the VALIDATED Pydantic Model
        return GapAnalysisResponse(
            missing_milestones=missing_milestones,
            compliance_score=int(coverage),
            risk_score=int(100 - coverage),
            total_found=found_count,
            gap_count=gap_count,
            next_priority=priority
        )

# Procedural wrapper for app.py
def detect_gaps(found_milestones: List[str], project_type: str = "structural") -> GapAnalysisResponse:
    engine = ComplianceGapEngine(project_type)
    return engine.detect_gaps(found_milestones)
