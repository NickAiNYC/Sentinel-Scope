from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class TenantContext(BaseModel):
    """Multi-tenant isolation context for enterprise deployments."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    tenant_id: str = Field(..., description="Unique tenant identifier (UUID or slug)")
    org_name: str = Field(..., min_length=1, description="Organization display name")
    tier: str = Field(
        ...,
        pattern="^(free|professional|enterprise)$",
        description="Subscription tier governing feature access",
    )


class ProjectProfile(BaseModel):
    """Construction project metadata aligned with NYC DOB records."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=False,
    )

    project_id: str = Field(..., description="Internal project identifier")
    bbl: str = Field(..., pattern=r"^\d{10}$", description="NYC Borough-Block-Lot identifier")
    address: str = Field(..., min_length=1, description="Site address")
    building_type: str = Field(..., description="Building classification (e.g., Residential, Commercial)")
    stories: int = Field(..., ge=1, description="Number of stories")
    year_built: int | None = Field(None, ge=1800, le=2100, description="Original construction year")
    permit_type: str = Field(..., description="Primary permit type (e.g., NB, A1, DM)")
    contractor_id: str = Field(..., description="Licensed contractor identifier")
    tenant_id: str = Field(..., description="Owning tenant identifier")


class ViolationRecord(BaseModel):
    """Normalized NYC DOB violation record."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    violation_id: str = Field(..., description="DOB violation number")
    project_id: str = Field(..., description="Associated project identifier")
    dob_class: str = Field(
        ...,
        pattern="^(Class A|Class B|Class C)$",
        description="NYC DOB Violation Class (A, B, or C)",
    )
    severity: str = Field(..., pattern="^(Critical|High|Medium|Low)$", description="Internal severity rating")
    description: str = Field(..., min_length=1, description="Violation description text")
    issue_date: date = Field(..., description="Date violation was issued")
    resolution_status: str = Field(
        ...,
        pattern="^(open|resolved|dismissed|appealed)$",
        description="Current resolution status",
    )
    resolved_date: date | None = Field(None, description="Date violation was resolved")


class InspectionRecord(BaseModel):
    """Inspection history entry tied to a project and permit."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    inspection_id: str = Field(..., description="Unique inspection identifier")
    project_id: str = Field(..., description="Associated project identifier")
    inspection_date: date = Field(..., description="Inspection date")
    result: str = Field(
        ...,
        pattern="^(pass|fail|partial|cancelled)$",
        description="Inspection outcome",
    )
    inspector: str = Field(..., min_length=1, description="Inspector name or badge ID")
    permit_ref: str = Field(..., description="Related permit reference number")
    notes: str | None = Field(None, description="Inspector notes or remarks")


class PermitRecord(BaseModel):
    """Permit details with computed age tracking."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=False,
    )

    permit_id: str = Field(..., description="DOB permit number")
    project_id: str = Field(..., description="Associated project identifier")
    issue_date: date = Field(..., description="Permit issue date")
    expiry_date: date = Field(..., description="Permit expiration date")
    permit_type: str = Field(..., description="Permit type code (e.g., NB, A1, DM)")
    status: str = Field(
        ...,
        pattern="^(active|expired|suspended|revoked)$",
        description="Current permit status",
    )

    @property
    def age_days(self) -> int:
        """Number of days since the permit was issued."""
        return (date.today() - self.issue_date).days


class RiskAssessment(BaseModel):
    """Output of the risk scoring engine for a given project."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    risk_score: int = Field(..., ge=0, le=100, description="Composite risk score (0=low, 100=critical)")
    stop_work_probability_30d: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of stop-work order within 30 days"
    )
    insurance_escalation_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of insurance premium escalation"
    )
    fine_exposure_estimate: float = Field(
        ..., ge=0.0, description="Estimated fine exposure in USD"
    )
    risk_drivers: list[str] = Field(
        default_factory=list, description="Top factors contributing to the risk score"
    )
    model_version: str = Field(..., description="Version of the risk model that produced this score")
    scored_at: datetime = Field(..., description="UTC timestamp when the score was computed")
    features_snapshot: dict = Field(
        ..., description="Feature vector snapshot used for scoring reproducibility"
    )


class ComplianceSnapshot(BaseModel):
    """Point-in-time compliance snapshot for forensic replay and audit."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    snapshot_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique snapshot identifier",
    )
    project_id: str = Field(..., description="Associated project identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of snapshot capture")
    data_hash: str = Field(
        ...,
        pattern=r"^[a-f0-9]{64}$",
        description="SHA-256 hex digest of raw_payload for integrity verification",
    )
    raw_payload: dict = Field(..., description="Complete raw data at time of capture")
    risk_assessment: RiskAssessment | None = Field(
        None, description="Risk assessment at time of capture, if available"
    )
    version: str = Field(..., description="Schema version for forward-compatible deserialization")




class AuditLogEntry(BaseModel):
    """Immutable audit log entry for compliance traceability."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )

    entry_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique audit entry identifier",
    )
    tenant_id: str = Field(..., description="Tenant that owns this audit event")
    actor: str = Field(..., min_length=1, description="User or service principal that performed the action")
    action: str = Field(..., min_length=1, description="Action performed (e.g., create, update, delete, export)")
    resource_type: str = Field(..., min_length=1, description="Type of resource acted upon (e.g., project, violation)")
    resource_id: str = Field(..., description="Identifier of the affected resource")
    timestamp: datetime = Field(..., description="UTC timestamp of the event")
    details: dict = Field(default_factory=dict, description="Arbitrary metadata about the event")
    ip_address: str | None = Field(None, description="Source IP address, if available")
