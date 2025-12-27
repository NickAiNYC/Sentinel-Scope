from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class CaptureClassification(BaseModel):
    milestone: str = Field(..., description="NYC Construction Milestone (e.g., Fireproofing)")
    mep_system: Optional[str] = None
    floor: str
    zone: str
    confidence: float = Field(..., ge=0, le=1) # Must be between 0.0 and 1.0
    compliance_relevance: int = Field(..., ge=1, le=5) # 1-5 scale
    evidence_notes: str

class ComplianceGap(BaseModel):
    milestone: str
    floor_range: str
    dob_code: str
    risk_level: str # e.g., "High", "Critical"
    deadline: str
    recommendation: str

class GapAnalysisResponse(BaseModel):
    missing_milestones: List[ComplianceGap]
    compliance_score: int
    risk_score: int
    next_priority: str

    @field_validator('compliance_score')
    @classmethod
    def validate_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Score must be between 0 and 100')
        return v
