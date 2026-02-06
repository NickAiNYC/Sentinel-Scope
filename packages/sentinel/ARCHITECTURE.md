# Vision-to-Compliance Bridge Architecture

## System Overview

The Vision-to-Compliance Bridge connects Sentinel-Scope's computer vision system with ConComplyAi's compliance database to provide real-time compliance monitoring from site camera feeds.

## Component Flow

```
┌─────────────────┐
│  Site Camera    │
│  Frame Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           VisionAgent                           │
│  • Processes frames with AI vision model        │
│  • Detects Workers and Equipment                │
│  • Extracts entity identifiers                  │
└────────┬────────────────────────────────────────┘
         │
         ▼ List[DetectedEntity]
┌─────────────────────────────────────────────────┐
│          EntityMatcher                          │
│  • Queries ConComplyAi database                 │
│  • Retrieves compliance status                  │
│  • Detects compliance gaps                      │
└────────┬────────────────────────────────────────┘
         │
         ▼ ComplianceStatus + ComplianceGap?
┌─────────────────────────────────────────────────┐
│         Gap Decision Logic                      │
│  IF: Compliance Gap Detected                    │
│    THEN: Trigger OutreachAgent                  │
└────────┬────────────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌─────────────────────────────────────┐
│Outreach│  │      DecisionProof Generator         │
│ Agent  │  │  • Creates immutable audit record    │
│        │  │  • Includes screenshot URL           │
│Notifies│  │  • Records timestamp                 │
│Supervisor│ │  • Links to all detection data      │
└────────┘  └──────────────────────────────────────┘
```

## Component Details

### 1. VisionAgent
**File:** `vision_agent.py`

**Responsibilities:**
- Accept site-cam frames (file paths or file-like objects)
- Process frames through AI vision model (DeepSeek)
- Detect and classify entities (Workers/Equipment)
- Extract visible identifiers (badges, equipment IDs)

**Key Methods:**
- `process_frame()` - Single frame processing
- `process_frames_batch()` - Batch processing for efficiency

**Output:** `List[DetectedEntity]`

### 2. EntityMatcher
**File:** `entity_matcher.py`

**Responsibilities:**
- Query ConComplyAi database for entity records
- Match detected entities with database entries
- Retrieve compliance status (insurance, certifications)
- Detect compliance gaps based on business rules

**Database Interface:**
```python
class DatabaseInterface(Protocol):
    def query_compliance_status(entity_id, entity_type) -> dict
```

**Key Methods:**
- `check_compliance()` - Query database for single entity
- `check_multiple()` - Batch compliance checking
- `detect_gaps()` - Identify compliance violations
- `find_all_gaps()` - Find gaps for multiple entities

**Gap Detection Rules:**
| Condition | Gap Type | Severity |
|-----------|----------|----------|
| insurance_status == "Expired" | Insurance Expired | Critical |
| insurance_status == "Pending" | Insurance Pending | High |
| certification_status == "Expired" | Certification Expired | High |
| certification_status == "None" | Certification Missing | Medium |

### 3. OutreachAgent
**File:** `outreach_agent.py`

**Responsibilities:**
- Format compliance gap notifications
- Send notifications to supervisors
- Support multiple notification channels
- Generate notification summaries

**Notification Interface:**
```python
class NotificationInterface(Protocol):
    def send_notification(recipient, subject, message) -> bool
```

**Key Methods:**
- `notify_gap()` - Send single gap notification
- `notify_multiple_gaps()` - Send multiple notifications
- `notify_critical_gaps_only()` - Filter for critical severity
- `send_summary_notification()` - Single summary for all gaps

### 4. VisionComplianceBridge
**File:** `bridge.py`

**Responsibilities:**
- Orchestrate all components
- Manage processing pipeline
- Generate DecisionProofs
- Maintain audit trail
- Produce audit reports

**Key Methods:**
- `process_frame()` - Complete pipeline for single frame
- `process_frames_batch()` - Batch processing
- `get_all_proofs()` - Retrieve all generated proofs
- `get_proofs_with_gaps()` - Filter for non-compliant detections
- `generate_audit_report()` - Create comprehensive report

## Data Models

### DetectedEntity
```python
{
    "entity_id": str,          # UUID
    "entity_type": str,        # "Worker" or "Equipment"
    "name": str,               # Identifier (badge #, equipment ID)
    "confidence": float,       # 0.0 - 1.0
    "location": str,           # Site zone/area
    "frame_timestamp": datetime
}
```

### ComplianceStatus
```python
{
    "entity_id": str,
    "entity_type": str,
    "is_compliant": bool,
    "insurance_status": str,      # "Active", "Expired", "Pending"
    "insurance_expiry": datetime,
    "certification_status": str,  # "Valid", "Expired", "None"
    "last_updated": datetime,
    "compliance_notes": str
}
```

### ComplianceGap
```python
{
    "gap_id": str,              # UUID
    "entity": DetectedEntity,
    "compliance_status": ComplianceStatus,
    "gap_type": str,            # "Insurance Expired", etc.
    "severity": str,            # "Critical", "High", "Medium", "Low"
    "detected_at": datetime,
    "description": str
}
```

### DecisionProof (Immutable)
```python
{
    "proof_id": str,            # UUID
    "entity": DetectedEntity,
    "compliance_status": ComplianceStatus | None,
    "gap": ComplianceGap | None,
    "screenshot_url": str,      # URL/path to frame
    "timestamp": datetime,
    "metadata": dict,
    "notification_sent": bool
}
```

## Integration Points

### ConComplyAi Database
Replace `MockDatabaseInterface` with your implementation:

```python
class ConComplyAiDatabase:
    def query_compliance_status(self, entity_id: str, entity_type: str):
        # Your database query logic
        # Return dict matching ComplianceStatus structure
        pass
```

### Notification System
Replace `MockNotificationService` with your implementation:

```python
class EmailNotificationService:
    def send_notification(self, recipient: str, subject: str, message: str):
        # Your notification logic (email, SMS, Slack, etc.)
        return True
```

## Processing Pipeline Example

```python
# Initialize bridge
bridge = VisionComplianceBridge(
    vision_api_key="your-api-key",
    database_interface=ConComplyAiDatabase(),
    notification_service=EmailService(),
    supervisor_contact="supervisor@example.com"
)

# Process frame
proofs = bridge.process_frame(
    frame_source="path/to/frame.jpg",
    screenshot_url="https://storage/frame-001.jpg",
    location="Zone A"
)

# Each proof contains:
for proof in proofs:
    print(f"Entity: {proof.entity.name}")
    print(f"Compliance: {proof.compliance_status.is_compliant}")
    if proof.gap:
        print(f"Gap: {proof.gap.gap_type} ({proof.gap.severity})")
        print(f"Notification sent: {proof.notification_sent}")
```

## Audit Trail

All detections generate immutable DecisionProofs:

1. **Screenshot URL** - Permanent link to the frame
2. **Timestamp** - When detection occurred
3. **Entity Data** - Complete detection details
4. **Compliance Status** - Database query results
5. **Gap Information** - If compliance issue detected
6. **Notification Record** - Whether supervisor was notified

This creates a complete, auditable chain of evidence for compliance reporting and legal requirements.

## Error Handling

- Vision model failures return empty entity list
- Database query failures return "Unknown" compliance status
- Notification failures are logged but don't block processing
- All errors maintain audit trail integrity

## Performance Considerations

- Batch processing for multiple frames
- Parallel vision model requests (configurable workers)
- Database query batching (via `check_multiple()`)
- Notification throttling (summary mode available)

## Security

- DecisionProofs are immutable (frozen=True)
- Screenshot URLs should use secure storage
- API keys managed through environment variables
- Database credentials separate from code

## Testing

Comprehensive test suite in `tests/test_vision_compliance.py`:

- Unit tests for each component
- Integration tests for full pipeline
- Mock services for isolated testing
- Edge case coverage

Run tests:
```bash
pytest tests/test_vision_compliance.py -v
```

## Future Enhancements

1. Real-time video stream processing
2. Historical trend analysis
3. Predictive compliance alerts
4. Multi-camera synchronization
5. Mobile app integration
6. Custom rule engine for gaps
