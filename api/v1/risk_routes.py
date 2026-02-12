"""Production risk & compliance API endpoints.

Routes:
    GET  /api/v1/projects/{project_id}/risk                  - Risk assessment
    GET  /api/v1/projects/{project_id}/compliance-status      - Compliance summary
    GET  /api/v1/projects/{project_id}/enforcement-forecast   - Enforcement forecast
    GET  /api/v1/portfolio/{tenant_id}/risk-index             - Portfolio risk summary
    POST /api/v1/webhooks/register                            - Register webhook
    GET  /api/v1/health                                       - Health check
    GET  /api/v1/metrics                                      - Prometheus metrics
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field

from core.enforcement_engine import EnforcementEngine
from risk_engine.engine import DeterministicRiskEngine

router = APIRouter(prefix="/api/v1", tags=["risk"])

_START_TIME = time.monotonic()
_REQUEST_COUNT = 0

# In-memory webhook store
_webhooks: dict[str, dict] = {}

# Shared engine instances
_risk_engine = DeterministicRiskEngine()
_enforcement_engine = EnforcementEngine()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class RiskAssessmentResponse(BaseModel):
    """Risk assessment output for a project."""

    project_id: str
    risk_score: int = Field(..., ge=0, le=100)
    stop_work_probability_30d: float = Field(..., ge=0.0, le=1.0)
    insurance_escalation_probability: float = Field(..., ge=0.0, le=1.0)
    fine_exposure_estimate: float = Field(..., ge=0.0)
    risk_drivers: list[str] = Field(default_factory=list)
    model_version: str
    scored_at: datetime
    features_snapshot: dict


class ComplianceStatusResponse(BaseModel):
    """Compliance summary for a project."""

    project_id: str
    status: str
    risk_level: str
    last_assessed: datetime


class EnforcementForecastResponse(BaseModel):
    """Enforcement forecast for a project."""

    project_id: str
    escalation_level: str
    likely_enforcement_actions: list[str] = Field(default_factory=list)
    stop_work_probability_30d: float
    stop_work_probability_60d: float
    recommended_actions: list[str] = Field(default_factory=list)
    timeline_days: int


class PortfolioRiskIndexResponse(BaseModel):
    """Portfolio-level risk summary."""

    tenant_id: str
    total_projects: int = 0
    avg_risk_score: float = 0.0
    high_risk_projects: int = 0


class WebhookRegisterRequest(BaseModel):
    """Webhook registration request."""

    url: str
    events: list[str]
    tenant_id: str


class WebhookRegisterResponse(BaseModel):
    """Webhook registration confirmation."""

    webhook_id: str
    url: str
    events: list[str]
    tenant_id: str
    registered_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _risk_level(score: int) -> str:
    """Derive human-readable risk level from a numeric score."""
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _increment_requests() -> None:
    global _REQUEST_COUNT  # noqa: PLW0603
    _REQUEST_COUNT += 1


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/risk",
    response_model=RiskAssessmentResponse,
)
def get_project_risk(
    project_id: str,
    violation_classes: str | None = Query(
        None, description="Comma-separated violation classes"
    ),
    permit_age_days: int = Query(0, ge=0),
    inspection_failures: int = Query(0, ge=0),
    inspection_total: int = Query(0, ge=0),
    milestone_delay_days: int = Query(0, ge=0),
    complaint_count_90d: int = Query(0, ge=0),
    prior_stop_work_orders: int = Query(0, ge=0),
    building_type: str = Query("commercial"),
    stories: int = Query(1, ge=1),
    contractor_violation_rate: float = Query(0.0, ge=0.0, le=1.0),
) -> RiskAssessmentResponse:
    """Return the deterministic risk assessment for a project."""
    _increment_requests()
    parsed_classes = (
        [v.strip() for v in violation_classes.split(",") if v.strip()]
        if violation_classes
        else []
    )
    assessment = _risk_engine.score_project(
        violation_classes=parsed_classes,
        permit_age_days=permit_age_days,
        inspection_failures=inspection_failures,
        inspection_total=inspection_total,
        milestone_delay_days=milestone_delay_days,
        complaint_count_90d=complaint_count_90d,
        prior_stop_work_orders=prior_stop_work_orders,
        building_type=building_type,
        stories=stories,
        contractor_violation_rate=contractor_violation_rate,
    )
    return RiskAssessmentResponse(
        project_id=project_id,
        risk_score=assessment.risk_score,
        stop_work_probability_30d=assessment.stop_work_probability_30d,
        insurance_escalation_probability=assessment.insurance_escalation_probability,
        fine_exposure_estimate=assessment.fine_exposure_estimate,
        risk_drivers=assessment.risk_drivers,
        model_version=assessment.model_version,
        scored_at=assessment.scored_at,
        features_snapshot=assessment.features_snapshot,
    )


@router.get(
    "/projects/{project_id}/compliance-status",
    response_model=ComplianceStatusResponse,
)
def get_compliance_status(project_id: str) -> ComplianceStatusResponse:
    """Return the compliance summary for a project."""
    _increment_requests()
    assessment = _risk_engine.score_project()
    return ComplianceStatusResponse(
        project_id=project_id,
        status="compliant" if assessment.risk_score < 50 else "non_compliant",
        risk_level=_risk_level(assessment.risk_score),
        last_assessed=datetime.now(tz=timezone.utc),
    )


@router.get(
    "/projects/{project_id}/enforcement-forecast",
    response_model=EnforcementForecastResponse,
)
def get_enforcement_forecast(
    project_id: str,
    violation_classes: str | None = Query(
        None, description="Comma-separated violation classes"
    ),
    permit_age_days: int = Query(0, ge=0),
    inspection_failures: int = Query(0, ge=0),
    inspection_total: int = Query(0, ge=0),
    milestone_delay_days: int = Query(0, ge=0),
    complaint_count_90d: int = Query(0, ge=0),
    prior_stop_work_orders: int = Query(0, ge=0),
    building_type: str = Query("commercial"),
    stories: int = Query(1, ge=1),
    contractor_violation_rate: float = Query(0.0, ge=0.0, le=1.0),
) -> EnforcementForecastResponse:
    """Return the enforcement forecast for a project."""
    _increment_requests()
    parsed_classes = (
        [v.strip() for v in violation_classes.split(",") if v.strip()]
        if violation_classes
        else []
    )
    assessment = _risk_engine.score_project(
        violation_classes=parsed_classes,
        permit_age_days=permit_age_days,
        inspection_failures=inspection_failures,
        inspection_total=inspection_total,
        milestone_delay_days=milestone_delay_days,
        complaint_count_90d=complaint_count_90d,
        prior_stop_work_orders=prior_stop_work_orders,
        building_type=building_type,
        stories=stories,
        contractor_violation_rate=contractor_violation_rate,
    )
    forecast = _enforcement_engine.forecast_enforcement(
        risk_score=assessment.risk_score,
        violation_classes=parsed_classes,
        prior_stop_work_orders=prior_stop_work_orders,
        permit_age_days=permit_age_days,
    )
    return EnforcementForecastResponse(
        project_id=project_id,
        escalation_level=forecast["escalation_level"],
        likely_enforcement_actions=forecast["likely_enforcement_actions"],
        stop_work_probability_30d=forecast["stop_work_probability_30d"],
        stop_work_probability_60d=forecast["stop_work_probability_60d"],
        recommended_actions=forecast["recommended_actions"],
        timeline_days=forecast["timeline_days"],
    )


@router.get(
    "/portfolio/{tenant_id}/risk-index",
    response_model=PortfolioRiskIndexResponse,
)
def get_portfolio_risk_index(tenant_id: str) -> PortfolioRiskIndexResponse:
    """Return portfolio-level risk summary (stub)."""
    _increment_requests()
    return PortfolioRiskIndexResponse(
        tenant_id=tenant_id,
        total_projects=0,
        avg_risk_score=0.0,
        high_risk_projects=0,
    )


@router.post(
    "/webhooks/register",
    response_model=WebhookRegisterResponse,
    status_code=201,
)
def register_webhook(
    request: WebhookRegisterRequest,
) -> WebhookRegisterResponse:
    """Register a webhook for event notifications."""
    _increment_requests()
    webhook_id = uuid4().hex
    now = datetime.now(tz=timezone.utc)
    _webhooks[webhook_id] = {
        "url": request.url,
        "events": request.events,
        "tenant_id": request.tenant_id,
        "registered_at": now.isoformat(),
    }
    return WebhookRegisterResponse(
        webhook_id=webhook_id,
        url=request.url,
        events=request.events,
        tenant_id=request.tenant_id,
        registered_at=now,
    )


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(tz=timezone.utc),
    )


@router.get("/metrics")
def metrics() -> Response:
    """Return Prometheus-compatible text metrics."""
    uptime_seconds = time.monotonic() - _START_TIME
    body = (
        "# HELP requests_total Total number of API requests.\n"
        "# TYPE requests_total counter\n"
        f"requests_total {_REQUEST_COUNT}\n"
        "# HELP uptime_seconds Time since process start in seconds.\n"
        "# TYPE uptime_seconds gauge\n"
        f"uptime_seconds {uptime_seconds:.2f}\n"
    )
    return Response(content=body, media_type="text/plain")
