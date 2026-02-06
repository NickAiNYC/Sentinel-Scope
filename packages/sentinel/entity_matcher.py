"""EntityMatcher: Queries ConComplyAi database for compliance status."""
import uuid
from datetime import datetime
from typing import List, Optional, Protocol

from packages.sentinel.models import ComplianceGap, ComplianceStatus, DetectedEntity


class DatabaseInterface(Protocol):
    """Protocol for ConComplyAi database interface."""
    
    def query_compliance_status(self, entity_id: str, entity_type: str) -> dict | None:
        """Query compliance status for an entity."""
        ...


class MockDatabaseInterface:
    """
    Mock database interface for ConComplyAi.
    Replace this with actual database implementation.
    """
    
    def query_compliance_status(self, entity_id: str, entity_type: str) -> dict | None:
        """
        Mock query that simulates database lookup.
        In production, this should query the actual ConComplyAi database.
        
        Args:
            entity_id: Entity identifier
            entity_type: "Worker" or "Equipment"
            
        Returns:
            Dictionary with compliance data or None if not found
        """
        # Mock data for demonstration
        # In production, replace with actual database query
        mock_data = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'is_compliant': False,  # Simulate non-compliant status
            'insurance_status': 'Expired',
            'insurance_expiry': datetime(2025, 1, 1),
            'certification_status': 'Valid',
            'last_updated': datetime.now(),
            'compliance_notes': 'Insurance expired - renewal required'
        }
        return mock_data


class EntityMatcher:
    """
    EntityMatcher takes detected objects (Workers/Equipment) and queries 
    the ConComplyAi database for their current Compliance Status.
    """
    
    def __init__(self, database_interface: DatabaseInterface | None = None):
        """
        Initialize EntityMatcher with database interface.
        
        Args:
            database_interface: Database interface for querying compliance status.
                              If None, uses MockDatabaseInterface.
        """
        self.db = database_interface or MockDatabaseInterface()
    
    def check_compliance(self, entity: DetectedEntity) -> ComplianceStatus:
        """
        Query ConComplyAi database for entity compliance status.
        
        Args:
            entity: Detected entity to check
            
        Returns:
            ComplianceStatus with current compliance information
        """
        # Query database for compliance status
        compliance_data = self.db.query_compliance_status(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type
        )
        
        if compliance_data:
            return ComplianceStatus(**compliance_data)
        else:
            # Return default unknown status if not found
            return ComplianceStatus(
                entity_id=entity.entity_id,
                entity_type=entity.entity_type,
                is_compliant=False,
                insurance_status='Unknown',
                certification_status='Unknown',
                last_updated=datetime.now(),
                compliance_notes='Entity not found in compliance database'
            )
    
    def check_multiple(self, entities: list[DetectedEntity]) -> list[tuple[DetectedEntity, ComplianceStatus]]:
        """
        Check compliance for multiple entities.
        
        Args:
            entities: List of detected entities
            
        Returns:
            List of tuples (entity, compliance_status)
        """
        results = []
        for entity in entities:
            compliance_status = self.check_compliance(entity)
            results.append((entity, compliance_status))
        return results
    
    def detect_gaps(
        self, 
        entity: DetectedEntity, 
        compliance_status: ComplianceStatus
    ) -> ComplianceGap | None:
        """
        Detect compliance gaps based on entity and compliance status.
        
        Args:
            entity: Detected entity
            compliance_status: Current compliance status
            
        Returns:
            ComplianceGap if gap detected, None otherwise
        """
        # Check for various compliance gaps
        gap_type = None
        severity = "Low"
        description = ""
        
        if compliance_status.insurance_status == "Expired":
            gap_type = "Insurance Expired"
            severity = "Critical"
            description = f"{entity.entity_type} '{entity.name}' present on site with expired insurance"
        elif compliance_status.insurance_status == "Pending":
            gap_type = "Insurance Pending"
            severity = "High"
            description = f"{entity.entity_type} '{entity.name}' has pending insurance status"
        elif compliance_status.certification_status == "Expired":
            gap_type = "Certification Expired"
            severity = "High"
            description = f"{entity.entity_type} '{entity.name}' has expired certification"
        elif compliance_status.certification_status == "None":
            gap_type = "Certification Missing"
            severity = "Medium"
            description = f"{entity.entity_type} '{entity.name}' missing required certification"
        
        if gap_type:
            return ComplianceGap(
                gap_id=str(uuid.uuid4()),
                entity=entity,
                compliance_status=compliance_status,
                gap_type=gap_type,
                severity=severity,
                detected_at=datetime.now(),
                description=description
            )
        
        return None
    
    def find_all_gaps(
        self, 
        entities: list[DetectedEntity]
    ) -> list[ComplianceGap]:
        """
        Find all compliance gaps for a list of entities.
        
        Args:
            entities: List of detected entities
            
        Returns:
            List of detected compliance gaps
        """
        gaps = []
        for entity in entities:
            compliance_status = self.check_compliance(entity)
            gap = self.detect_gaps(entity, compliance_status)
            if gap:
                gaps.append(gap)
        return gaps
