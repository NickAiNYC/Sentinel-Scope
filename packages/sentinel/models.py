"""Data models for Sentinel Vision-to-Compliance bridge."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DetectedEntity(BaseModel):
    """Represents a detected object from site-cam frames."""
    model_config = ConfigDict(str_strip_whitespace=True)

    entity_id: str = Field(..., description="Unique identifier for the detected entity")
    entity_type: str = Field(..., description="Type of entity: 'Worker' or 'Equipment'")
    name: str | None = Field(None, description="Name or identifier of the entity")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence score")
    location: str = Field(..., description="Location where entity was detected")
    frame_timestamp: datetime = Field(..., description="Timestamp of the frame")


class ComplianceStatus(BaseModel):
    """Represents compliance status from ConComplyAi database."""
    model_config = ConfigDict(str_strip_whitespace=True)

    entity_id: str
    entity_type: str
    is_compliant: bool = Field(..., description="Overall compliance status")
    insurance_status: str = Field(..., description="Insurance status: 'Active', 'Expired', 'Pending'")
    insurance_expiry: datetime | None = Field(None, description="Insurance expiration date")
    certification_status: str = Field(..., description="Certification status: 'Valid', 'Expired', 'None'")
    last_updated: datetime = Field(..., description="Last update timestamp")
    compliance_notes: str = Field(default="", description="Additional compliance notes")


class ComplianceGap(BaseModel):
    """Represents a detected compliance gap."""
    model_config = ConfigDict(str_strip_whitespace=True)

    gap_id: str = Field(..., description="Unique gap identifier")
    entity: DetectedEntity
    compliance_status: ComplianceStatus
    gap_type: str = Field(..., description="Type of gap: e.g., 'Insurance Expired', 'Certification Missing'")
    severity: str = Field(..., description="Severity: 'Critical', 'High', 'Medium', 'Low'")
    detected_at: datetime = Field(..., description="When the gap was detected")
    description: str = Field(..., description="Human-readable gap description")


class DecisionProof(BaseModel):
    """Audit trail for visual detections with screenshot URL and timestamp."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        frozen=True  # Immutable for audit trail integrity
    )

    proof_id: str = Field(..., description="Unique proof identifier")
    entity: DetectedEntity
    compliance_status: ComplianceStatus | None = Field(None, description="Compliance status if checked")
    gap: ComplianceGap | None = Field(None, description="Compliance gap if detected")
    screenshot_url: str = Field(..., description="URL or path to the screenshot/frame")
    timestamp: datetime = Field(..., description="Proof creation timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata for the audit trail")
    notification_sent: bool = Field(default=False, description="Whether notification was triggered")
