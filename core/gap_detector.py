"""
SentinelScope Gap Detector
Analyzes classified milestones against NYC Building Code 2022 requirements.
"""

from typing import List, Dict, Any

class ComplianceGapEngine:
    # Industry-standard requirements mapped to NYC Building Code 2022
    NYC_REQUIREMENTS = {
        "structural": {
            "Foundation": {"code": "BC Chapter 18", "criticality": "high"},
            "Structural Steel": {"code": "BC Chapter 22", "criticality": "high"},
            "Fireproofing": {"code": "BC Section 704", "criticality": "critical"},
            "Decking": {"code": "BC Section 2210", "criticality": "medium"},
            "Enclosure": {"code": "BC Chapter 14", "criticality": "medium"}
        },
        "mep": {
            "MEP Rough-in": {"code": "NYC Mechanical Code", "criticality": "high"},
            "Fire Protection": {"code": "BC Chapter 9", "criticality": "critical"},
            "Electrical Distribution": {"code": "NYC Electrical Code", "criticality": "high"},
            "HVAC Installation": {"code": "MC Chapter 6", "criticality": "medium"}
        }
    }

    def __init__(self, project_type: str = "structural"):
        self.project_type = project_type.lower()
        self.rules = self.NYC_REQUIREMENTS.get(self.project_type, self.NYC_REQUIREMENTS["structural"])

    def detect_gaps(self, found_milestones: List[str]) -> Dict[str, Any]:
        found_normalized = [m.lower() for m in found_milestones]
        missing_details = []
        
        for req, info in self.rules.items():
            # Check for partial string matches (e.g., "Fireproofing Spray" matches "Fireproofing")
            if not any(req.lower() in f_norm or f_norm in req.lower() for f_norm in found_normalized):
                missing_details.append({
                    "milestone": req,
                    "code": info["code"],
                    "criticality": info["criticality"]
                })

        total_req = len(self.rules)
        coverage = ((total_req - len(missing_details)) / total_req) * 100
        
        return {
            "coverage_percentage": round(coverage, 1),
            "risk_level": self._calculate_risk(coverage, missing_details),
            "gaps": missing_details,
            "recommendation": self._get_recommendation(missing_details)
        }

    def _calculate_risk(self, coverage: float, gaps: List[Dict]) -> str:
        # If any 'critical' item like Fireproofing is missing, it's automatic HIGH risk
        if any(g["criticality"] == "critical" for g in gaps):
            return "🔴 HIGH (Safety Critical)"
        if coverage >= 85: return "🟢 LOW"
        if coverage >= 60: return "🟡 MEDIUM"
        return "🔴 HIGH"

    def _get_recommendation(self, gaps: List[Dict]) -> str:
        if not gaps: return "Project evidence is sufficient for DOB audit."
        critical_items = [g['milestone'] for g in gaps if g['criticality'] == 'critical']
        if critical_items:
            return f"URGENT: Missing evidence for {', '.join(critical_items)}. Insurance coverage at risk."
        return "Capture remaining milestones to reach 100% compliance."

# Procedural wrapper for app.py
def detect_gaps(found_milestones: List[str], project_type: str = "structural"):
    engine = ComplianceGapEngine(project_type)
    return engine.detect_gaps(found_milestones)
