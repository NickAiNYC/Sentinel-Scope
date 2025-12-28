from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional
from typing_extensions import Self

class CaptureClassification(BaseModel):
    """Data structure for AI-tagged site images used for forensic evidence."""
    model_config = ConfigDict(
        populate_by_name=True, 
        str_strip_whitespace=True,
        frozen=False
    )

    milestone: str = Field(..., description="NYC Construction Milestone (e.g., Fireproofing)")
    mep_system: Optional[str] = None
    # Supports floor codes like 04, PH (Penthouse), SC (Sub-Cellar), M (Mezzanine)
    floor: str = Field(..., pattern=r"^[0-9RCBLMPHSC]+$") 
    zone: str = Field(..., description="Site quadrant (North, Core, Hoist, etc.)")
    confidence: float = Field(..., ge=0, le=1) 
    compliance_relevance: int = Field(..., ge=1, le=5, description="1: Low, 5: Life Safety Critical")
    evidence_notes: str

class ComplianceGap(BaseModel):
    """Maps a missing requirement to NYC DOB Violation Classes."""
    milestone: str
    floor_range: str
    dob_code: str
    risk_level: str = Field(..., pattern="^(Critical|High|Medium|Low)$") 
    dob_class: str = Field("Class B", description="NYC DOB Violation Class (A, B, or C)")
    deadline: str
    recommendation: str

class GapAnalysisResponse(BaseModel):
    """Final output from ComplianceGapEngine for the Streamlit Dashboard."""
    missing_milestones: List[ComplianceGap]
    compliance_score: int = Field(..., ge=0, le=100)
    risk_score: int = Field(..., ge=0, le=100)
    total_found: int
    gap_count: int
    next_priority: str

    @field_validator('compliance_score', 'risk_score', mode='after')
    @classmethod
    def validate_scores(cls, v: int) -> int:
        """Ensures scores remain within valid integer bounds."""
        return v

    @model_validator(mode='after')
    def check_score_logic(self) -> Self:
        """
        Forensic Logic: Auto-escalates Risk Score if Critical gaps exist.
        Ensures the dashboard accurately reflects Life Safety hazards.
        """
        has_critical = any(gap.risk_level == "Critical" for gap in self.missing_milestones)
        
        if has_critical:
            # Enforce a minimum Risk Score of 75 for Critical (Class A) hazards
            self.risk_score = max(self.risk_score, 75)
            
            # Find the first critical gap to highlight in the dashboard header
            try:
                critical_gap = next(g for g in self.missing_milestones if g.risk_level == "Critical")
                self.next_priority = f"🚨 URGENT: {critical_gap.milestone} ({critical_gap.dob_class})"
            except StopIteration:
                pass
             
        return self
