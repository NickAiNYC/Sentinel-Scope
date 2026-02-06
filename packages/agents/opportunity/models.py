"""
Data models for opportunity classification with skeptical-by-default philosophy.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OpportunityLevel(str, Enum):
    """
    Conservative opportunity classification levels.
    Default assumption: CLOSED unless proven otherwise.
    """
    CLOSED = "CLOSED"  # Not open for bidding, pre-solicitation
    SOFT_OPEN = "SOFT_OPEN"  # May be open but unclear, proceed with caution
    CONTESTABLE = "CONTESTABLE"  # Confirmed open and biddable


class AgencyType(str, Enum):
    """NYC Agencies with different insurance/license requirements."""
    SCA = "SCA"  # School Construction Authority
    DDC = "DDC"  # Department of Design and Construction
    DEP = "DEP"  # Department of Environmental Protection
    DOT = "DOT"  # Department of Transportation
    NYCHA = "NYCHA"  # New York City Housing Authority
    OTHER = "OTHER"


class DecisionProof(BaseModel):
    """
    Audit trail for opportunity classification decisions.
    Mirrors the DecisionProof pattern used for compliance checks.
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    decision: OpportunityLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Skeptical analysis of why this classification was chosen")
    text_signals: List[str] = Field(default_factory=list, description="Key phrases that informed decision")
    red_flags: List[str] = Field(default_factory=list, description="Warning signs indicating closure or barriers")
    ai_model: str = Field(default="claude-4-5-opus-20251101")
    
    model_config = {"frozen": True}  # Immutable audit records


class OpportunityClassification(BaseModel):
    """
    Complete opportunity assessment with skeptical prompt analysis.
    """
    project_id: str
    project_title: str
    agency: AgencyType
    opportunity_level: OpportunityLevel
    decision_proof: DecisionProof
    raw_text: str = Field(..., description="Original agency text analyzed")
    estimated_value: Optional[float] = None
    trade_category: Optional[str] = None  # e.g., "General Construction", "Electrical", "HVAC"
    
    # Metadata
    classification_timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = {"frozen": False}  # Allow updates for feasibility scoring
