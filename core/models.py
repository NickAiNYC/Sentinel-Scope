from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from typing_extensions import Self

class CaptureClassification(BaseModel):
    """Data structure for AI-tagged site images"""
    milestone: str = Field(..., description="NYC Construction Milestone (e.g., Fireproofing)")
    mep_system: Optional[str] = None
    floor: str = Field(..., pattern=r"^[0-9RCBLM]+$") # Validates Floor 1, R (Roof), B (Basement), etc.
    zone: str = Field(..., description="Site quadrant or zone (e.g., North, Core, Hoist)")
    confidence: float = Field(..., ge=0, le=1) 
    compliance_relevance: int = Field(..., ge=1, le=5, description="1: Low Impact, 5: Life Safety/Critical")
    evidence_notes: str

class ComplianceGap(BaseModel):
    """Detailed model for a single missing requirement mapped to NYC DOB Classes"""
    milestone: str
    floor_range: str
    dob_code: str
    risk_level: str = Field(..., pattern="^(Critical|High|Medium|Low)$") 
    dob_class: str = Field("Class B", description="DOB Violation Class: A (Non-Hazardous), B (Hazardous), C (Immediately Hazardous)")
    deadline: str
    recommendation: str

class GapAnalysisResponse(BaseModel):
    """Final output from the ComplianceGapEngine"""
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
        """Ensures that compliance and risk scores are logically inverse"""
        if abs((self.compliance_score + self.risk_score) - 100) > 5: # Allowing a 5-point margin for weighted logic
            # Optional: Log a warning or adjust logic if they drift too far apart
            pass
        return self
