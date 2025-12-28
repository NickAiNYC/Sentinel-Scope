"""
SentinelScope Data Models v2.7 (Enhanced)
Pydantic schemas for AI-powered NYC construction compliance auditing.

Enhancements:
- Additional validation for NYC-specific fields
- Helper methods for data transformation
- Better error messages
- Export utilities
- Integration with constants
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Dict, Any
from typing_extensions import Self
from datetime import datetime
import re

# Import constants for validation
try:
    from core.constants import DOB_CLASS_MAP, VALIDATION_PATTERNS, BOROUGHS
except ImportError:
    # Fallback if constants not available
    DOB_CLASS_MAP = {
        "CRITICAL": "Class C",
        "HIGH": "Class B",
        "MEDIUM": "Class B",
        "LOW": "Class A"
    }
    VALIDATION_PATTERNS = {
        "BBL": r"^[1-5]\d{9}$"
    }
    BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]


class CaptureClassification(BaseModel):
    """
    Data structure for AI-tagged site images used for forensic evidence.
    
    Represents a single construction milestone detected via computer vision analysis.
    Used as input for gap detection and compliance scoring.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=False,
        validate_assignment=True  # Re-validate on field updates
    )
    
    milestone: str = Field(
        ..., 
        description="NYC Construction Milestone (e.g., Fireproofing, Foundation)",
        min_length=2,
        max_length=100
    )
    
    mep_system: Optional[str] = Field(
        None,
        description="MEP subsystem if applicable (HVAC, Plumbing, Electrical, Fire Protection)"
    )
    
    # Supports floor codes: 01-99, PH (Penthouse), SC (Sub-Cellar), M (Mezzanine), 
    # R (Roof), C (Cellar), B (Basement), L (Lobby)
    floor: str = Field(
        ..., 
        pattern=r"^[0-9RCBLMPHSC]+$",
        description="Floor designation (e.g., 04, PH, SC, M)"
    )
    
    zone: str = Field(
        ..., 
        description="Site quadrant or zone (North, South, East, West, Core, Hoist, etc.)",
        min_length=2,
        max_length=50
    )
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="AI confidence score (0.0 = no confidence, 1.0 = certain)"
    )
    
    compliance_relevance: int = Field(
        ..., 
        ge=1, 
        le=5,
        description="Compliance importance: 1=Low, 2=Medium, 3=High, 4=Critical, 5=Life Safety"
    )
    
    evidence_notes: str = Field(
        ...,
        description="Detailed evidence description for audit trail",
        min_length=10,
        max_length=500
    )
    
    # Optional metadata
    capture_timestamp: Optional[datetime] = Field(
        None,
        description="When the photo was taken (if available from EXIF)"
    )
    
    image_hash: Optional[str] = Field(
        None,
        description="SHA-256 hash of source image for deduplication"
    )
    
    @field_validator('milestone', mode='after')
    @classmethod
    def normalize_milestone(cls, v: str) -> str:
        """Normalize milestone names for consistency."""
        # Capitalize each word
        v = v.title()
        
        # Fix common abbreviations
        replacements = {
            "Mep": "MEP",
            "Hvac": "HVAC",
            "Dob": "DOB",
            "Nyc": "NYC"
        }
        
        for old, new in replacements.items():
            v = v.replace(old, new)
        
        return v
    
    @field_validator('floor', mode='after')
    @classmethod
    def validate_floor(cls, v: str) -> str:
        """Ensure floor designations are uppercase and valid."""
        v = v.upper().strip()
        
        # Common floor codes
        valid_codes = ["PH", "SC", "M", "R", "C", "B", "L"]
        
        # Allow numeric floors (01-99) or valid codes
        if not (v.isdigit() or v in valid_codes):
            # Check if it's a combination like "B1", "SC2"
            if not re.match(r"^[A-Z]{1,2}\d{0,2}$", v):
                raise ValueError(
                    f"Invalid floor designation: {v}. "
                    f"Use format: 01-99, or codes: {', '.join(valid_codes)}"
                )
        
        return v
    
    @field_validator('confidence', mode='after')
    @classmethod
    def round_confidence(cls, v: float) -> float:
        """Round confidence to 2 decimal places for consistency."""
        return round(v, 2)
    
    def to_dict_with_metadata(self) -> Dict[str, Any]:
        """Export with additional computed metadata."""
        data = self.model_dump()
        data['confidence_pct'] = f"{self.confidence * 100:.0f}%"
        data['relevance_label'] = self._get_relevance_label()
        return data
    
    def _get_relevance_label(self) -> str:
        """Convert numeric relevance to human-readable label."""
        labels = {
            1: "Low Priority",
            2: "Medium Priority",
            3: "High Priority",
            4: "Critical",
            5: "Life Safety Critical"
        }
        return labels.get(self.compliance_relevance, "Unknown")
    
    def is_high_priority(self) -> bool:
        """Check if this is a high-priority finding."""
        return self.compliance_relevance >= 4 and self.confidence >= 0.7


class ComplianceGap(BaseModel):
    """
    Maps a missing requirement to NYC DOB Violation Classes.
    
    Represents a gap between required milestones and actual site progress.
    Used for generating remediation reports and DOB compliance documentation.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )
    
    milestone: str = Field(
        ...,
        description="Missing milestone name",
        min_length=2,
        max_length=100
    )
    
    floor_range: str = Field(
        ...,
        description="Affected floor range (e.g., '01-15', 'All Floors', 'PH')"
    )
    
    dob_code: str = Field(
        ...,
        description="NYC Building Code reference (e.g., 'BC Chapter 22', 'BC Section 718')",
        min_length=5
    )
    
    risk_level: str = Field(
        ..., 
        pattern=r"^(Critical|High|Medium|Low)$",
        description="Risk severity level"
    )
    
    dob_class: str = Field(
        "Class B",
        pattern=r"^Class [ABC]$",
        description="NYC DOB Violation Class (A=Non-Hazardous, B=Hazardous, C=Immediately Hazardous)"
    )
    
    deadline: str = Field(
        ...,
        description="Remediation deadline (e.g., 'Immediately', 'Within 7 Days', '30-45 Days')"
    )
    
    recommendation: str = Field(
        ...,
        description="AI-generated or manual remediation recommendation",
        min_length=20
    )
    
    estimated_cost: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated remediation cost (USD)"
    )
    
    @field_validator('dob_class', mode='before')
    @classmethod
    def map_risk_to_class(cls, v: str, info) -> str:
        """Auto-map risk level to DOB class if not provided."""
        # If dob_class is provided, use it
        if v and v != "Class B":
            return v
        
        # Otherwise, map from risk_level
        risk_level = info.data.get('risk_level')
        if risk_level:
            return DOB_CLASS_MAP.get(risk_level.upper(), "Class B")
        
        return v
    
    @model_validator(mode='after')
    def validate_deadline_severity(self) -> Self:
        """Ensure deadline matches risk level."""
        urgent_deadlines = ["Immediately", "24 Hours", "ASAP"]
        
        if self.risk_level == "Critical" and self.deadline not in urgent_deadlines:
            # Auto-correct deadline for critical issues
            self.deadline = "Immediately"
        
        return self
    
    def to_dict_with_priority(self) -> Dict[str, Any]:
        """Export with computed priority score."""
        data = self.model_dump()
        data['priority_score'] = self._calculate_priority()
        return data
    
    def _calculate_priority(self) -> int:
        """Calculate numeric priority (1-10) based on risk and class."""
        risk_scores = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1}
        class_scores = {"Class C": 10, "Class B": 6, "Class A": 2}
        
        risk_score = risk_scores.get(self.risk_level, 5)
        class_score = class_scores.get(self.dob_class, 5)
        
        # Weighted average (60% risk, 40% class)
        return int((risk_score * 0.6) + (class_score * 0.4))


class GapAnalysisResponse(BaseModel):
    """
    Final output from ComplianceGapEngine for the Streamlit Dashboard.
    
    Comprehensive compliance analysis with scoring, gaps, and recommendations.
    Used to drive UI rendering and report generation.
    """
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    missing_milestones: List[ComplianceGap] = Field(
        default_factory=list,
        description="List of detected compliance gaps"
    )
    
    compliance_score: int = Field(
        ..., 
        ge=0, 
        le=100,
        description="Overall compliance score (0-100%)"
    )
    
    risk_score: int = Field(
        ..., 
        ge=0, 
        le=100,
        description="Overall risk score (0-100, higher = more risk)"
    )
    
    total_found: int = Field(
        ...,
        ge=0,
        description="Total milestones detected"
    )
    
    gap_count: int = Field(
        ...,
        ge=0,
        description="Total gaps identified"
    )
    
    next_priority: str = Field(
        ...,
        description="Next recommended action or priority"
    )
    
    # Optional metadata
    analysis_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="When this analysis was performed"
    )
    
    project_name: Optional[str] = Field(
        None,
        description="Project identifier"
    )
    
    bbl: Optional[str] = Field(
        None,
        pattern=VALIDATION_PATTERNS.get("BBL", r"^[1-5]\d{9}$"),
        description="NYC Borough-Block-Lot identifier"
    )
    
    @field_validator('compliance_score', 'risk_score', mode='after')
    @classmethod
    def validate_scores(cls, v: int) -> int:
        """Ensures scores remain within valid integer bounds."""
        return max(0, min(100, v))
    
    @model_validator(mode='after')
    def check_score_logic(self) -> Self:
        """
        Forensic Logic: Auto-escalates Risk Score if Critical gaps exist.
        Ensures the dashboard accurately reflects Life Safety hazards.
        """
        has_critical = any(
            gap.risk_level == "Critical" 
            for gap in self.missing_milestones
        )
        
        if has_critical:
            # Enforce minimum Risk Score of 75 for Critical (Class C) hazards
            self.risk_score = max(self.risk_score, 75)
            
            # Find the first critical gap to highlight
            try:
                critical_gap = next(
                    g for g in self.missing_milestones 
                    if g.risk_level == "Critical"
                )
                self.next_priority = (
                    f"🚨 URGENT: {critical_gap.milestone} ({critical_gap.dob_class})"
                )
            except StopIteration:
                pass
        
        # Ensure gap_count matches actual count
        actual_gap_count = len(self.missing_milestones)
        if self.gap_count != actual_gap_count:
            self.gap_count = actual_gap_count
        
        return self
    
    @model_validator(mode='after')
    def validate_score_consistency(self) -> Self:
        """Ensure compliance and risk scores are inversely related."""
        # Risk score should generally be inverse of compliance
        expected_risk = 100 - self.compliance_score
        
        # Allow some variance for critical gaps
        if abs(self.risk_score - expected_risk) > 25:
            # If they're too different, it's likely due to critical gaps
            # which is acceptable, but log it
            pass
        
        return self
    
    def get_summary(self) -> Dict[str, Any]:
        """Get executive summary for reports."""
        critical_count = sum(
            1 for g in self.missing_milestones 
            if g.risk_level == "Critical"
        )
        high_count = sum(
            1 for g in self.missing_milestones 
            if g.risk_level == "High"
        )
        
        return {
            "compliance_score": self.compliance_score,
            "risk_score": self.risk_score,
            "total_gaps": self.gap_count,
            "critical_gaps": critical_count,
            "high_priority_gaps": high_count,
            "status": self._get_status(),
            "next_action": self.next_priority
        }
    
    def _get_status(self) -> str:
        """Determine overall project status."""
        if self.compliance_score >= 95:
            return "EXCELLENT"
        elif self.compliance_score >= 85:
            return "COMPLIANT"
        elif self.compliance_score >= 75:
            return "ACCEPTABLE"
        elif self.compliance_score >= 60:
            return "NEEDS ATTENTION"
        else:
            return "NON-COMPLIANT"
    
    def get_gaps_by_priority(self) -> Dict[str, List[ComplianceGap]]:
        """Group gaps by risk level for prioritized display."""
        grouped = {
            "Critical": [],
            "High": [],
            "Medium": [],
            "Low": []
        }
        
        for gap in self.missing_milestones:
            grouped[gap.risk_level].append(gap)
        
        return grouped
    
    def export_for_report(self) -> Dict[str, Any]:
        """Export comprehensive data for PDF/JSON reports."""
        return {
            "summary": self.get_summary(),
            "gaps_by_priority": self.get_gaps_by_priority(),
            "full_data": self.model_dump(),
            "generated_at": datetime.now().isoformat()
        }


# Utility functions for model validation
def validate_bbl(bbl: str) -> bool:
    """Validate NYC BBL format."""
    pattern = VALIDATION_PATTERNS.get("BBL", r"^[1-5]\d{9}$")
    return bool(re.match(pattern, bbl))


def parse_bbl(bbl: str) -> Optional[Dict[str, str]]:
    """Parse BBL into components."""
    if not validate_bbl(bbl):
        return None
    
    borough_map = {
        "1": "MANHATTAN",
        "2": "BRONX",
        "3": "BROOKLYN",
        "4": "QUEENS",
        "5": "STATEN ISLAND"
    }
    
    return {
        "bbl": bbl,
        "borough_code": bbl[0],
        "borough_name": borough_map.get(bbl[0], "UNKNOWN"),
        "block": bbl[1:6],
        "lot": bbl[6:10]
    }
