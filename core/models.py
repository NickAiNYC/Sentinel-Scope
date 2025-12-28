from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional
from typing_extensions import Self

class CaptureClassification(BaseModel):
    """Data structure for AI-tagged site images used for forensic evidence."""
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    milestone: str = Field(..., description="NYC Construction Milestone (e.g., Fireproofing)")
    mep_system: Optional[str] = None
    # Optimized pattern for 2025: Handles floors like PH (Penthouse), SC (Sub-cellar), 
    # and standard 0-9RCBLM codes.
    floor: str = Field(..., pattern=r"^[0-9RCBLMPHSC]+$") 
    zone: str = Field(..., description="Site quadrant or zone (e.g., North, Core, Hoist)")
    confidence: float = Field(..., ge=0, le=1) 
    compliance_relevance: int = Field(..., ge=1, le=5, description="1: Low Impact, 5: Life Safety/Critical")
    evidence_notes: str

class ComplianceGap(BaseModel):
    """Detailed model for a single missing requirement mapped to NYC DOB Classes."""
    milestone: str
    floor_range: str
    dob_code: str
    risk_level: str = Field(..., pattern="^(Critical|High|Medium|Low)$") 
    # NYC DOB Class logic: A (Non-Hazardous), B (Hazardous), C (Immediately Hazardous)
    dob_class: str = Field("Class B", description="DOB Violation Class")
    deadline: str
    recommendation: str

class GapAnalysisResponse(BaseModel):
    """Final output from the ComplianceGapEngine passed to the Streamlit UI."""
    missing_milestones: List[ComplianceGap]
    compliance_score: int = Field(..., ge=0, le=100)
    risk_score: int = Field(..., ge=0, le=100)
    total_found: int
    gap_count: int
    next_priority: str

    @field_validator('compliance_score', 'risk_score')
    @classmethod
    def validate_scores(cls, v: int) -> int:
        # Pydantic v2 handles the range check via Field(ge=0, le=100), 
        # so this is now strictly for custom business logic if needed.
        return v

    @model_validator(mode='after')
    def check_score_logic(self) -> Self:
        """
        Ensures that compliance and risk scores stay logically aligned.
        If a 'Critical' gap exists, risk_score is elevated regardless of compliance %.
        """
        has_critical = any(gap.risk_level == "Critical" for gap in self.missing_milestones)
        
        # Logic: If there is a critical safety gap, the risk score should reflect high risk
        # even if 90% of other milestones are finished.
        if has_critical and self.risk_score < 50:
             # Auto-correct risk score to reflect life-safety priority
             self.risk_score = max(self.risk_score, 75)
             
        return self
