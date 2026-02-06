"""Sentinel Vision-to-Compliance bridge module."""
from packages.sentinel.bridge import VisionComplianceBridge
from packages.sentinel.entity_matcher import (
    DatabaseInterface,
    EntityMatcher,
    MockDatabaseInterface,
)
from packages.sentinel.models import (
    ComplianceGap,
    ComplianceStatus,
    DecisionProof,
    DetectedEntity,
)
from packages.sentinel.outreach_agent import (
    MockNotificationService,
    NotificationInterface,
    OutreachAgent,
)
from packages.sentinel.vision_agent import VisionAgent

__all__ = [
    'VisionAgent',
    'EntityMatcher',
    'DatabaseInterface',
    'MockDatabaseInterface',
    'OutreachAgent',
    'NotificationInterface',
    'MockNotificationService',
    'VisionComplianceBridge',
    'DecisionProof',
    'DetectedEntity',
    'ComplianceStatus',
    'ComplianceGap',
]
