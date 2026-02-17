"""
Site Evidence Upload API for SiteSentinel-AI

Handles construction site image uploads with SHA-256 hashing
and integrates with the VisualScoutAgent pipeline.
"""

import hashlib
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel

from services.orchestrator.graph import run_compliance_pipeline


router = APIRouter(prefix="/api/sites", tags=["sites", "evidence"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EvidenceUploadResponse(BaseModel):
    """Response from evidence upload endpoint."""
    
    evidence_id: str
    site_id: str
    org_id: str
    image_url: str
    sha256_hash: str
    analysis_status: str  # "pending" | "completed" | "failed"
    
    # Analysis results (if completed)
    visual_findings: Optional[str] = None
    guard_status: Optional[str] = None
    risk_level: Optional[str] = None
    proof_id: Optional[str] = None


class ComplianceAnalysisResponse(BaseModel):
    """Response from compliance analysis."""
    
    site_id: str
    org_id: str
    proof_id: str
    sha256_hash: str
    
    # Visual Scout results
    visual_findings: Optional[str] = None
    milestones_detected: list[str] = []
    violations_detected: list[str] = []
    confidence_score: float = 0.0
    
    # Guard results
    guard_status: str
    compliance_violations: list[str] = []
    required_actions: list[str] = []
    risk_level: str
    
    # Remediation
    remediation_plan: Optional[str] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_org_id() -> str:
    """
    Get current organization ID from request context.
    
    In production, this would:
    - Extract from JWT token
    - Validate against database
    - Set PostgreSQL session variable for RLS
    
    For now, returns a placeholder.
    """
    # TODO: Implement JWT token extraction
    # For demo: return a test org_id
    return os.getenv("DEFAULT_ORG_ID", "00000000-0000-0000-0000-000000000001")


def upload_to_storage(file: UploadFile, site_id: str) -> str:
    """
    Upload image to S3/Cloudinary.
    
    In production, this would:
    - Upload to S3 with site_id prefix
    - Or upload to Cloudinary with transformations
    - Return public URL
    
    For now, saves locally and returns file path.
    """
    # TODO: Implement S3/Cloudinary upload
    
    # Create upload directory
    upload_dir = "/tmp/site_evidence"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{site_id}_{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    
    # Return file:// URL for local processing
    return f"file://{filepath}"


def calculate_sha256(file: UploadFile) -> str:
    """Calculate SHA-256 hash of uploaded file."""
    file.file.seek(0)  # Reset to beginning
    file_content = file.file.read()
    file.file.seek(0)  # Reset again for future reads
    
    return hashlib.sha256(file_content).hexdigest()


async def store_evidence_in_db(
    evidence_id: str,
    site_id: str,
    org_id: str,
    image_url: str,
    sha256_hash: str,
    analysis_json: dict
) -> None:
    """
    Store evidence in PostgreSQL with RLS.
    
    In production, this would:
    - Set app.current_org_id session variable
    - INSERT into site_evidence table
    - RLS policy ensures org isolation
    """
    # TODO: Implement PostgreSQL storage
    # Placeholder for database operation
    pass


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/{site_id}/upload-evidence", response_model=EvidenceUploadResponse)
async def upload_site_evidence(
    site_id: str,
    file: UploadFile = File(..., description="Site photo (JPEG/PNG)"),
    org_id: str = Depends(get_current_org_id)
) -> EvidenceUploadResponse:
    """
    Upload construction site evidence image.
    
    This endpoint:
    1. Uploads image to S3/Cloudinary
    2. Calculates SHA-256 hash for audit trail
    3. Triggers VisualScoutAgent analysis
    4. Stores results in site_evidence table with RLS
    
    Args:
        site_id: Site UUID
        file: Image file upload
        org_id: Organization ID (from JWT token)
    
    Returns:
        EvidenceUploadResponse with analysis results
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG/PNG)"
        )
    
    # Generate evidence ID
    evidence_id = str(uuid.uuid4())
    
    # Calculate SHA-256 hash
    try:
        sha256_hash = calculate_sha256(file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate hash: {str(e)}"
        )
    
    # Upload to storage
    try:
        image_url = upload_to_storage(file, site_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )
    
    # Run compliance pipeline
    try:
        analysis_result = await run_compliance_pipeline(
            site_id=site_id,
            org_id=org_id,
            image_url=image_url
        )
        
        # Store in database
        await store_evidence_in_db(
            evidence_id=evidence_id,
            site_id=site_id,
            org_id=org_id,
            image_url=image_url,
            sha256_hash=sha256_hash,
            analysis_json=analysis_result
        )
        
        return EvidenceUploadResponse(
            evidence_id=evidence_id,
            site_id=site_id,
            org_id=org_id,
            image_url=image_url,
            sha256_hash=sha256_hash,
            analysis_status="completed",
            visual_findings=analysis_result.get("visual_findings"),
            guard_status=analysis_result.get("guard_status"),
            risk_level=analysis_result.get("risk_level"),
            proof_id=analysis_result.get("proof_id")
        )
    
    except Exception as e:
        # Store with failed status
        await store_evidence_in_db(
            evidence_id=evidence_id,
            site_id=site_id,
            org_id=org_id,
            image_url=image_url,
            sha256_hash=sha256_hash,
            analysis_json={"error": str(e)}
        )
        
        return EvidenceUploadResponse(
            evidence_id=evidence_id,
            site_id=site_id,
            org_id=org_id,
            image_url=image_url,
            sha256_hash=sha256_hash,
            analysis_status="failed"
        )


@router.get("/{site_id}/compliance", response_model=ComplianceAnalysisResponse)
async def get_site_compliance(
    site_id: str,
    org_id: str = Depends(get_current_org_id)
) -> ComplianceAnalysisResponse:
    """
    Get latest compliance analysis for a site.
    
    This endpoint:
    - Queries site_evidence table with RLS
    - Returns most recent analysis results
    - Shows current compliance status
    
    Args:
        site_id: Site UUID
        org_id: Organization ID (from JWT token, enforced by RLS)
    
    Returns:
        ComplianceAnalysisResponse with latest results
    """
    # TODO: Implement database query with RLS
    # Placeholder response
    raise HTTPException(
        status_code=501,
        detail="Compliance query not yet implemented"
    )
