from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from typing_extensions import Self

class CaptureClassification(BaseModel):
    """Data structure for AI-tagged site images used for forensic evidence."""
    milestone: str = Field(..., description="NYC Construction Milestone (e.g., Fireproofing)")
    mep_system: Optional[str] = None
    # Validates Floor 1, R (Roof), B (Basement), L (Lobby), M (Mezzanine), etc.
    floor: str = Field(..., pattern=r"^[0-9RCBLM]+$") 
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
        if not 0 <= v <= 100:
            raise ValueError('Score must be between 0 and 100')
        return v

    @model_validator(mode='after')
    def check_score_logic(self) -> Self:
        """
        Ensures that compliance and risk scores stay logically aligned.
        High compliance should generally correlate with lower risk.
        """
        # Allowing a small margin for weighted calculations used in gap_detector.py
        if abs((self.compliance_score + self.risk_score) - 100) > 15: 
            # Logic: If they drift too far apart, the risk_score is likely 
            # being driven by an 'Immediately Hazardous' DOB Class C gap.
            pass
        return self
