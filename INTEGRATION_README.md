# 🏗️ SiteSentinel-AI: Scope Vision Integration

## 🎯 Overview

This integration merges the standalone "Scope" computer vision module into SiteSentinel-AI's multi-agent compliance platform. The result is a **unified multi-modal pipeline** that analyzes both visual evidence AND permit/legal data for NYC construction sites.

## 🧠 Multi-Modal Agent Pipeline

**The only NYC compliance platform that SEES + READS + PROVES:**

```
PHOTO UPLOAD → VISUAL SCOUT (DeepSeek-V3)
       ↓
 LEGAL GUARD (LL149/152 + BC 2022)
       ↓
 FIXER (Remediation)
       ↓
 SHA-256 PROOF (DOB/Insurance)
```

### Unified Coverage
- **Portfolio Risk**: Permit data + DOB violations
- **Site Vision**: Construction photo analysis
- **Regulatory Reasoning**: NYC BC 2022 Chapter 33 compliance

## 💰 Economics Story

```
BEFORE (Scope standalone):  $0.0007 per permit/doc
NOW (Integrated):           $0.0007 per doc + $0.0012 per photo = $0.0019 total
STILL:                      500x cheaper than manual compliance audits ($1,000+)
```

**Cost Breakdown:**
- DeepSeek-V3 Vision: $0.0012 per image
- Document analysis: $0.0007 per permit/doc
- **Total per site audit**: ~$0.0019
- **Manual audit cost**: $500-$2,000
- **ROI**: 99.9% cost reduction

## 🏗️ Architecture

### 1. Backend: Vision Agent (`services/agents/visual_scout.py`)

**Refactored from Scope's `core/gap_detector.py` and `core/processor.py`**

```python
from services.agents.visual_scout import VisualScoutAgent

agent = VisualScoutAgent()

result = await agent.run({
    "site_id": "uuid-here",
    "org_id": "org-uuid",
    "image_url": "https://s3.../site-photo.jpg"
})

# Returns:
# {
#   "visual_findings": "MILESTONE: Foundation\nSAFETY_STATUS: Compliant...",
#   "milestones_detected": ["Foundation", "MEP Rough-in"],
#   "violations_detected": ["BC §3314.1: Missing fall protection"],
#   "confidence_score": 0.85,
#   "requires_legal_verification": True
# }
```

**Features:**
- ✅ DeepSeek-V3 Vision API integration
- ✅ NYC Building Code Chapter 33 focused prompts
- ✅ Parallel image processing (5 workers)
- ✅ Graceful degradation (no image = skip)
- ✅ Confidence scoring (0.0-1.0)

### 2. Backend: Database (`migrations/003_add_site_evidence.sql`)

**Multi-tenant evidence storage with Row-Level Security (RLS)**

```sql
CREATE TABLE site_evidence (
    id UUID PRIMARY KEY,
    site_id UUID NOT NULL,
    org_id UUID NOT NULL,  -- RLS enforced
    image_url TEXT NOT NULL,
    analysis_json JSONB,
    sha256_hash TEXT UNIQUE,  -- Audit trail
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policy: Tenant Isolation
CREATE POLICY tenant_isolation_policy ON site_evidence
    USING (org_id = current_setting('app.current_org_id')::uuid);
```

**Features:**
- ✅ PostgreSQL with RLS for multi-tenancy
- ✅ SHA-256 hashing for tamper-proof evidence
- ✅ JSONB storage for structured findings
- ✅ Indexed for performance (site_id, org_id, created_at)

### 3. Backend: LangGraph Orchestration (`services/orchestrator/graph.py`)

**State-based workflow with conditional routing**

```python
from services.orchestrator.graph import build_compliance_graph, run_compliance_pipeline

# Build graph
graph = build_compliance_graph()

# Workflow: visual_scout → guard → fixer → proof

# Execute pipeline
result = await run_compliance_pipeline(
    site_id="uuid",
    org_id="org-uuid",
    image_url="https://s3.../photo.jpg"  # Optional
)
```

**Routing Logic:**
- `visual_scout` → `guard` (if successful)
- `guard` → `fixer` (if pass/warning)
- `guard` → END (if fail/critical violations)
- `fixer` → `proof` → END

### 4. Backend: API Endpoint (`api/v1/evidence_routes.py`)

**RESTful upload with automatic pipeline execution**

```bash
POST /api/sites/{site_id}/upload-evidence
Content-Type: multipart/form-data

# Request
file: <binary image data>

# Response
{
  "evidence_id": "uuid",
  "site_id": "uuid",
  "org_id": "uuid",
  "image_url": "https://s3.../photo.jpg",
  "sha256_hash": "abc123...",
  "analysis_status": "completed",
  "visual_findings": "MILESTONE: Foundation...",
  "guard_status": "pass",
  "risk_level": "Low",
  "proof_id": "proof-uuid"
}
```

### 5. Frontend: Agent Theater (`apps/dashboard/components/AgentTheater.tsx`)

**Real-time visual orchestration timeline**

**Features:**
- ✅ Drag-and-drop image upload
- ✅ Real-time agent status via WebSocket
- ✅ Animated node transitions (pulsing during execution)
- ✅ Vision findings display with confidence bar
- ✅ "Skip Vision" button for graceful degradation

**Components:**
- `AgentTheater.tsx`: Main orchestration UI
- `ImageUpload.tsx`: Evidence upload with preview

## 🚦 Validation & Safety

### Graceful Degradation
```typescript
// If NO image uploaded, visual_scout passes state forward
handleSkipVision() {
    setAgents({
        visual_scout: { status: 'skipped' },
        guard: { status: 'active' }  // Continue pipeline
    });
}
```

### No Breaking Changes to LL149/152
- Guard agent validates independently
- Existing LL149/152 logic untouched
- Vision findings are ADDITIVE, not replacing

### Testing Requirements
```bash
# Backend tests
pytest tests/test_visual_scout.py
pytest tests/test_guard_agent.py
pytest tests/test_graph_orchestration.py

# Frontend tests
npm test -- AgentTheater.test.tsx
npm test -- ImageUpload.test.tsx

# Integration tests
pytest tests/test_end_to_end_vision_pipeline.py
```

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
# Python backend
pip install httpx langgraph pydantic fastapi

# Frontend (if applicable)
npm install --save react

```

### 2. Environment Variables

```bash
# .env
DEEPSEEK_API_KEY=your_deepseek_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/sitesentinel
DEFAULT_ORG_ID=00000000-0000-0000-0000-000000000001
```

### 3. Database Migration

```bash
# Run the migration
psql -U postgres -d sitesentinel -f migrations/003_add_site_evidence.sql

# Verify RLS
psql -U postgres -d sitesentinel -c "\d site_evidence"
```

### 4. Start Services

```bash
# Backend API
uvicorn app:app --reload --port 8000

# Frontend (if separate)
npm run dev
```

## 🔬 Usage Examples

### Example 1: Full Vision Pipeline

```python
import asyncio
from services.orchestrator.graph import run_compliance_pipeline

async def analyze_site():
    result = await run_compliance_pipeline(
        site_id="site-123",
        org_id="org-456",
        image_url="https://example.com/site-photo.jpg"
    )
    
    print(f"Vision Findings: {result['visual_findings']}")
    print(f"Guard Status: {result['guard_status']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Proof ID: {result['proof_id']}")
    print(f"SHA-256: {result['sha256_hash']}")

asyncio.run(analyze_site())
```

### Example 2: Skip Vision (Graceful Degradation)

```python
# No image_url provided
result = await run_compliance_pipeline(
    site_id="site-123",
    org_id="org-456",
    image_url=None  # Visual Scout will skip
)

# Pipeline continues: guard → fixer → proof
```

### Example 3: Frontend Integration

```tsx
import { AgentTheater } from './components/AgentTheater';

function SiteDashboard() {
  const handleComplete = (result) => {
    console.log('Analysis complete:', result);
    // Show proof certificate, update UI, etc.
  };

  return (
    <AgentTheater
      siteId="site-123"
      orgId="org-456"
      onAnalysisComplete={handleComplete}
    />
  );
}
```

## 🔐 Security & Compliance

### Row-Level Security (RLS)
Every query automatically enforces org_id isolation:

```sql
-- User from Org A
SET app.current_org_id = 'org-a-uuid';
SELECT * FROM site_evidence;  -- Only sees Org A's evidence

-- User from Org B  
SET app.current_org_id = 'org-b-uuid';
SELECT * FROM site_evidence;  -- Only sees Org B's evidence
```

### SHA-256 Audit Trail
Every piece of evidence is hashed:

```python
import hashlib

sha256_hash = hashlib.sha256(image_bytes).hexdigest()
# Stored in site_evidence.sha256_hash for tamper detection
```

### Data Retention
- Images: Stored in S3 with 7-year retention (DOB requirement)
- Analysis: JSONB in PostgreSQL, indexed for compliance queries
- Proofs: Immutable SHA-256 hashes for legal verification

## 📊 Monitoring & Observability

### Key Metrics
- Vision API latency (target: <2s per image)
- Guard failure rate (target: <5%)
- Pipeline completion rate (target: >95%)
- Cost per analysis (target: $0.002)

### Logging
```python
# Each agent logs execution
logger.info("VisualScout started", extra={
    "site_id": site_id,
    "org_id": org_id,
    "image_url": image_url
})
```

## 🚀 Next Steps

### Immediate
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Performance testing (100 concurrent uploads)
- [ ] Security audit (RLS verification)

### Future Enhancements
- [ ] Multi-image batch analysis
- [ ] Video frame extraction
- [ ] Drone footage integration
- [ ] 3D site model generation
- [ ] Automated DOB filing

## 📞 Support

For questions or issues:
- Technical: support@sitesentinel.ai
- Security: security@sitesentinel.ai
- Sales: sales@sitesentinel.ai

---

**Built with ❤️ for NYC General Contractors**
