"""
Vision Agent API endpoints for Sentinel-Scope.

Routes:
    POST /api/v1/vision/analyze   - Single site photo analysis
    POST /api/v1/vision/batch     - Batch processing of multiple photos
    GET  /api/v1/vision/compliance/{bbl} - Site compliance summary by BBL
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from packages.vision_agent_bridge import VisionAgentBridge

router = APIRouter(prefix="/api/v1/vision", tags=["vision"])

# Shared bridge instance (replaced at app startup for production)
_bridge = VisionAgentBridge()


def get_bridge() -> VisionAgentBridge:
    """Return the active VisionAgentBridge instance."""
    return _bridge


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """Single image analysis request."""

    bbl: str = Field(..., description="NYC BBL identifier")
    address: str = Field(default="", description="Human-readable address")
    image_url: str = Field(default="", description="URL or base64 image data")
    findings: list[dict[str, Any]] = Field(default_factory=list)
    violations: list[dict[str, Any]] = Field(default_factory=list)
    compliance_score: float = Field(default=0.0, ge=0, le=100)
    risk_score: float = Field(default=0.0, ge=0, le=100)


class BatchRequest(BaseModel):
    """Batch analysis request."""

    bbl: str = Field(..., description="NYC BBL identifier")
    address: str = Field(default="")
    images: list[str] = Field(default_factory=list, description="Image URLs or paths")
    findings: list[dict[str, Any]] = Field(default_factory=list)
    violations: list[dict[str, Any]] = Field(default_factory=list)
    dob_violations: list[dict[str, Any]] = Field(default_factory=list)
    compliance_score: float = Field(default=0.0, ge=0, le=100)
    risk_score: float = Field(default=0.0, ge=0, le=100)


class AnalyzeResponse(BaseModel):
    """Response from analysis endpoints."""

    analysis_id: str
    bbl: str
    proof_id: str | None = None
    sha256_hash: str | None = None
    compliance_score: float
    risk_score: float
    summary: str = ""


class ComplianceResponse(BaseModel):
    """Response for compliance summary endpoint."""

    bbl: str
    status: str
    analyses: int = 0
    proofs: int = 0
    latest_compliance_score: float | None = None
    latest_risk_score: float | None = None
    total_images: int = 0
    total_findings: int = 0
    total_violations: int = 0
    cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_site_photo(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a single site photo and run the full 5-agent pipeline."""
    bridge = get_bridge()
    proof = bridge.run_full_pipeline(
        bbl=request.bbl,
        address=request.address,
        images_processed=1,
        findings=request.findings,
        violations=request.violations,
        compliance_score=request.compliance_score,
        risk_score=request.risk_score,
    )
    if proof is None:
        raise HTTPException(status_code=500, detail="Pipeline failed")

    return AnalyzeResponse(
        analysis_id=proof.analysis_id,
        bbl=proof.bbl,
        proof_id=proof.proof_id,
        sha256_hash=proof.sha256_hash,
        compliance_score=proof.compliance_score,
        risk_score=proof.risk_score,
        summary=proof.summary,
    )


@router.post("/batch", response_model=AnalyzeResponse)
def batch_analyze(request: BatchRequest) -> AnalyzeResponse:
    """Batch-process multiple site photos through the 5-agent pipeline."""
    bridge = get_bridge()
    proof = bridge.run_full_pipeline(
        bbl=request.bbl,
        address=request.address,
        images_processed=len(request.images),
        findings=request.findings,
        violations=request.violations,
        dob_violations=request.dob_violations,
        compliance_score=request.compliance_score,
        risk_score=request.risk_score,
    )
    if proof is None:
        raise HTTPException(status_code=500, detail="Batch pipeline failed")

    return AnalyzeResponse(
        analysis_id=proof.analysis_id,
        bbl=proof.bbl,
        proof_id=proof.proof_id,
        sha256_hash=proof.sha256_hash,
        compliance_score=proof.compliance_score,
        risk_score=proof.risk_score,
        summary=proof.summary,
    )


@router.get("/compliance/{bbl}", response_model=ComplianceResponse)
def get_compliance_summary(bbl: str) -> ComplianceResponse:
    """Return aggregated compliance data for a BBL."""
    bridge = get_bridge()
    data = bridge.get_site_compliance(bbl)
    return ComplianceResponse(**data)
