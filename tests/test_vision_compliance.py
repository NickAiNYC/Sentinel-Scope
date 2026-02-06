"""Tests for Vision-to-Compliance Bridge components."""
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from packages.sentinel.models import (
    DetectedEntity, 
    ComplianceStatus, 
    ComplianceGap,
    DecisionProof
)
from packages.sentinel.entity_matcher import EntityMatcher, MockDatabaseInterface
from packages.sentinel.outreach_agent import OutreachAgent, MockNotificationService
from packages.sentinel.bridge import VisionComplianceBridge


# ===== FIXTURES =====

@pytest.fixture
def sample_entity():
    """Create a sample detected entity."""
    return DetectedEntity(
        entity_id=str(uuid.uuid4()),
        entity_type="Worker",
        name="Worker-123",
        confidence=0.95,
        location="Zone A",
        frame_timestamp=datetime.now()
    )


@pytest.fixture
def compliant_status():
    """Create a compliant status."""
    return ComplianceStatus(
        entity_id=str(uuid.uuid4()),
        entity_type="Worker",
        is_compliant=True,
        insurance_status="Active",
        certification_status="Valid",
        last_updated=datetime.now(),
        compliance_notes="All requirements met"
    )


@pytest.fixture
def non_compliant_status():
    """Create a non-compliant status with expired insurance."""
    return ComplianceStatus(
        entity_id=str(uuid.uuid4()),
        entity_type="Worker",
        is_compliant=False,
        insurance_status="Expired",
        insurance_expiry=datetime(2025, 1, 1),
        certification_status="Valid",
        last_updated=datetime.now(),
        compliance_notes="Insurance expired"
    )


@pytest.fixture
def entity_matcher():
    """Create an EntityMatcher instance."""
    return EntityMatcher(database_interface=MockDatabaseInterface())


@pytest.fixture
def outreach_agent():
    """Create an OutreachAgent instance."""
    return OutreachAgent(notification_service=MockNotificationService())


# ===== MODEL TESTS =====

def test_detected_entity_creation(sample_entity):
    """Test DetectedEntity model creation."""
    assert sample_entity.entity_type == "Worker"
    assert sample_entity.name == "Worker-123"
    assert sample_entity.confidence == 0.95
    assert sample_entity.location == "Zone A"


def test_compliance_status_creation(compliant_status):
    """Test ComplianceStatus model creation."""
    assert compliant_status.is_compliant is True
    assert compliant_status.insurance_status == "Active"
    assert compliant_status.certification_status == "Valid"


def test_decision_proof_immutability():
    """Test that DecisionProof is immutable (frozen)."""
    from pydantic import ValidationError
    
    entity = DetectedEntity(
        entity_id=str(uuid.uuid4()),
        entity_type="Worker",
        name="Test",
        confidence=0.9,
        location="Zone A",
        frame_timestamp=datetime.now()
    )
    
    proof = DecisionProof(
        proof_id=str(uuid.uuid4()),
        entity=entity,
        screenshot_url="http://example.com/screenshot.jpg",
        timestamp=datetime.now()
    )
    
    # Try to modify and expect ValidationError due to frozen=True
    with pytest.raises(ValidationError):
        proof.notification_sent = True


# ===== ENTITY MATCHER TESTS =====

def test_entity_matcher_check_compliance(entity_matcher, sample_entity):
    """Test EntityMatcher can check compliance status."""
    status = entity_matcher.check_compliance(sample_entity)
    
    assert isinstance(status, ComplianceStatus)
    assert status.entity_id == sample_entity.entity_id
    assert status.entity_type == sample_entity.entity_type


def test_entity_matcher_detect_insurance_gap(entity_matcher, sample_entity, non_compliant_status):
    """Test EntityMatcher detects insurance expiration gap."""
    gap = entity_matcher.detect_gaps(sample_entity, non_compliant_status)
    
    assert gap is not None
    assert gap.gap_type == "Insurance Expired"
    assert gap.severity == "Critical"
    assert "expired insurance" in gap.description.lower()


def test_entity_matcher_no_gap_for_compliant(entity_matcher, sample_entity, compliant_status):
    """Test EntityMatcher returns None for compliant entities."""
    gap = entity_matcher.detect_gaps(sample_entity, compliant_status)
    
    assert gap is None


def test_entity_matcher_find_all_gaps(entity_matcher):
    """Test EntityMatcher can find gaps for multiple entities."""
    entities = [
        DetectedEntity(
            entity_id=str(uuid.uuid4()),
            entity_type="Worker",
            name=f"Worker-{i}",
            confidence=0.9,
            location="Zone A",
            frame_timestamp=datetime.now()
        )
        for i in range(3)
    ]
    
    gaps = entity_matcher.find_all_gaps(entities)
    
    # Mock database returns expired insurance for all
    assert len(gaps) == 3
    assert all(gap.gap_type == "Insurance Expired" for gap in gaps)


# ===== OUTREACH AGENT TESTS =====

def test_outreach_agent_notify_gap(outreach_agent, sample_entity, non_compliant_status):
    """Test OutreachAgent can send gap notification."""
    gap = ComplianceGap(
        gap_id=str(uuid.uuid4()),
        entity=sample_entity,
        compliance_status=non_compliant_status,
        gap_type="Insurance Expired",
        severity="Critical",
        detected_at=datetime.now(),
        description="Worker present with expired insurance"
    )
    
    result = outreach_agent.notify_gap(gap)
    
    assert result is True


def test_outreach_agent_notify_multiple_gaps(outreach_agent, sample_entity, non_compliant_status):
    """Test OutreachAgent can notify multiple gaps."""
    gaps = [
        ComplianceGap(
            gap_id=str(uuid.uuid4()),
            entity=sample_entity,
            compliance_status=non_compliant_status,
            gap_type="Insurance Expired",
            severity="Critical",
            detected_at=datetime.now(),
            description=f"Gap {i}"
        )
        for i in range(3)
    ]
    
    results = outreach_agent.notify_multiple_gaps(gaps)
    
    assert results['total'] == 3
    assert results['successful'] == 3
    assert results['failed'] == 0


def test_outreach_agent_critical_only(outreach_agent, sample_entity, non_compliant_status):
    """Test OutreachAgent filters critical gaps."""
    gaps = [
        ComplianceGap(
            gap_id=str(uuid.uuid4()),
            entity=sample_entity,
            compliance_status=non_compliant_status,
            gap_type="Insurance Expired",
            severity="Critical" if i < 2 else "Medium",
            detected_at=datetime.now(),
            description=f"Gap {i}"
        )
        for i in range(4)
    ]
    
    results = outreach_agent.notify_critical_gaps_only(gaps)
    
    # Only 2 critical gaps should be notified
    assert results['total'] == 2
    assert results['successful'] == 2


def test_outreach_agent_summary_notification(outreach_agent, sample_entity, non_compliant_status):
    """Test OutreachAgent creates summary notification."""
    gaps = [
        ComplianceGap(
            gap_id=str(uuid.uuid4()),
            entity=sample_entity,
            compliance_status=non_compliant_status,
            gap_type="Insurance Expired",
            severity="Critical",
            detected_at=datetime.now(),
            description=f"Gap {i}"
        )
        for i in range(2)
    ]
    
    result = outreach_agent.send_summary_notification(gaps)
    
    assert result is True


# ===== VISION COMPLIANCE BRIDGE TESTS =====

@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_bridge_process_frame(mock_process_frame, sample_entity):
    """Test VisionComplianceBridge processes frame end-to-end."""
    # Mock the vision agent to return our sample entity
    mock_process_frame.return_value = [sample_entity]
    
    bridge = VisionComplianceBridge(
        vision_api_key="test-key",
        supervisor_contact="test@example.com"
    )
    
    proofs = bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg",
        location="Zone A"
    )
    
    assert len(proofs) == 1
    assert isinstance(proofs[0], DecisionProof)
    assert proofs[0].entity == sample_entity
    assert proofs[0].screenshot_url == "http://example.com/screenshot.jpg"


@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_bridge_stores_proofs(mock_process_frame, sample_entity):
    """Test VisionComplianceBridge stores DecisionProofs."""
    mock_process_frame.return_value = [sample_entity]
    
    bridge = VisionComplianceBridge(vision_api_key="test-key")
    
    bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg"
    )
    
    all_proofs = bridge.get_all_proofs()
    assert len(all_proofs) == 1


@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_bridge_get_proofs_with_gaps(mock_process_frame, sample_entity):
    """Test VisionComplianceBridge filters proofs with gaps."""
    mock_process_frame.return_value = [sample_entity]
    
    bridge = VisionComplianceBridge(vision_api_key="test-key")
    
    # Process frame - mock database returns expired insurance
    bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg"
    )
    
    proofs_with_gaps = bridge.get_proofs_with_gaps()
    assert len(proofs_with_gaps) >= 1
    assert all(proof.gap is not None for proof in proofs_with_gaps)


@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_bridge_audit_report(mock_process_frame, sample_entity):
    """Test VisionComplianceBridge generates audit report."""
    mock_process_frame.return_value = [sample_entity]
    
    bridge = VisionComplianceBridge(vision_api_key="test-key")
    
    bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg"
    )
    
    report = bridge.generate_audit_report()
    
    assert 'total_detections' in report
    assert 'gaps_detected' in report
    assert 'entity_type_breakdown' in report
    assert 'proofs' in report
    assert report['total_detections'] == 1


@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_bridge_clear_proofs(mock_process_frame, sample_entity):
    """Test VisionComplianceBridge can clear stored proofs."""
    mock_process_frame.return_value = [sample_entity]
    
    bridge = VisionComplianceBridge(vision_api_key="test-key")
    
    bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg"
    )
    
    assert len(bridge.get_all_proofs()) > 0
    
    bridge.clear_proofs()
    assert len(bridge.get_all_proofs()) == 0


# ===== INTEGRATION TEST =====

@patch('packages.sentinel.vision_agent.VisionAgent.process_frame')
def test_full_integration(mock_process_frame):
    """Test complete integration flow: detect -> check -> notify -> proof."""
    # Create test entities
    entities = [
        DetectedEntity(
            entity_id=str(uuid.uuid4()),
            entity_type="Worker",
            name="Worker-001",
            confidence=0.95,
            location="Zone A",
            frame_timestamp=datetime.now()
        ),
        DetectedEntity(
            entity_id=str(uuid.uuid4()),
            entity_type="Equipment",
            name="Crane-42",
            confidence=0.88,
            location="Zone B",
            frame_timestamp=datetime.now()
        )
    ]
    
    mock_process_frame.return_value = entities
    
    # Create bridge
    bridge = VisionComplianceBridge(
        vision_api_key="test-key",
        supervisor_contact="supervisor@test.com"
    )
    
    # Process frame
    proofs = bridge.process_frame(
        frame_source="test_frame.jpg",
        screenshot_url="http://example.com/screenshot.jpg",
        location="Construction Site A"
    )
    
    # Verify results
    assert len(proofs) == 2
    
    # Check that all entities were processed
    entity_types = {proof.entity.entity_type for proof in proofs}
    assert "Worker" in entity_types
    assert "Equipment" in entity_types
    
    # Verify DecisionProofs have required fields
    for proof in proofs:
        assert proof.proof_id is not None
        assert proof.screenshot_url == "http://example.com/screenshot.jpg"
        assert proof.timestamp is not None
        assert proof.entity is not None
        assert proof.compliance_status is not None
    
    # Generate audit report
    report = bridge.generate_audit_report()
    assert report['total_detections'] == 2
