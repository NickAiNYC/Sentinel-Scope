"""
Construction Intelligence API endpoints.

Routes:
    GET  /api/v1/intel/opportunities     - SCA/DDC/EDA project feed
    POST /api/v1/intel/bid-analysis      - Bid/no-bid recommendation
    GET  /api/v1/intel/competitor/{bbl}   - Site activity intelligence
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/intel", tags=["intel"])


class OpportunityItem(BaseModel):
    """A single opportunity in the project feed."""

    project_id: str
    agency: str
    title: str
    estimated_value: float | None = None
    opportunity_level: str = "CLOSED"
    trade_category: str = ""


class OpportunityFeedResponse(BaseModel):
    """Response for the opportunity feed endpoint."""

    total: int = 0
    opportunities: list[OpportunityItem] = Field(default_factory=list)


class BidAnalysisRequest(BaseModel):
    """Request for bid/no-bid recommendation."""

    project_id: str
    agency: str = ""
    title: str = ""
    estimated_value: float | None = None
    contractor_trades: list[str] = Field(default_factory=list)
    contractor_capacity: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Available capacity 0-1"
    )


class BidAnalysisResponse(BaseModel):
    """Bid/no-bid recommendation response."""

    project_id: str
    recommendation: str = "NO_BID"
    confidence: float = 0.0
    reasoning: str = ""
    win_probability: float = 0.0


class CompetitorIntelResponse(BaseModel):
    """Competitor activity intelligence for a BBL."""

    bbl: str
    active_permits: int = 0
    recent_violations: int = 0
    estimated_project_value: float | None = None
    notes: str = ""


@router.get("/opportunities", response_model=OpportunityFeedResponse)
def list_opportunities() -> OpportunityFeedResponse:
    """Return available SCA/DDC/EDA project opportunities."""
    # In production this queries the OpportunityClassifier; returns
    # a static placeholder for now.
    return OpportunityFeedResponse(total=0, opportunities=[])


@router.post("/bid-analysis", response_model=BidAnalysisResponse)
def bid_analysis(request: BidAnalysisRequest) -> BidAnalysisResponse:
    """
    Evaluate whether to bid on a project.

    Factors: contractor trades, capacity, project requirements.
    """
    # Simple heuristic – real implementation calls OpportunityClassifier
    has_trade_match = bool(request.contractor_trades)
    has_capacity = request.contractor_capacity > 0.3

    if has_trade_match and has_capacity:
        recommendation = "BID"
        confidence = min(0.9, request.contractor_capacity)
        win_prob = round(confidence * 0.8, 2)
        reasoning = "Trade match and sufficient capacity."
    else:
        recommendation = "NO_BID"
        confidence = 0.6
        win_prob = 0.0
        reasoning = (
            "Insufficient trade coverage or capacity for this project."
        )

    return BidAnalysisResponse(
        project_id=request.project_id,
        recommendation=recommendation,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        win_probability=win_prob,
    )


@router.get("/competitor/{bbl}", response_model=CompetitorIntelResponse)
def competitor_intel(bbl: str) -> CompetitorIntelResponse:
    """Return competitor activity intelligence for a BBL."""
    return CompetitorIntelResponse(
        bbl=bbl,
        notes="No competitor data available. Query DOB permits for live data.",
    )
