# 🚀 SiteSentinel-AI Integration Transfer Guide

## 📋 Overview

This document provides step-by-step instructions for transferring the Scope Vision Integration files from the `Sentinel-Scope` repository to the `SiteSentinel-AI` repository.

## 📦 Files to Transfer

### Backend (Python)
```
Source: Sentinel-Scope/                  Destination: SiteSentinel-AI/
├── services/agents/
│   ├── __init__.py                  →   services/agents/__init__.py
│   ├── base_agent.py                →   services/agents/base_agent.py
│   ├── visual_scout.py              →   services/agents/visual_scout.py
│   └── guard_agent.py               →   services/agents/guard_agent.py
├── services/orchestrator/
│   ├── __init__.py                  →   services/orchestrator/__init__.py
│   └── graph.py                     →   services/orchestrator/graph.py
├── api/v1/
│   └── evidence_routes.py           →   api/v1/evidence_routes.py
├── migrations/
│   └── 003_add_site_evidence.sql    →   migrations/003_add_site_evidence.sql
└── tests/
    └── test_vision_integration.py   →   tests/test_vision_integration.py
```

### Frontend (TypeScript/React)
```
Source: Sentinel-Scope/                  Destination: SiteSentinel-AI/
└── apps/dashboard/components/
    ├── AgentTheater.tsx             →   apps/dashboard/components/AgentTheater.tsx
    └── ImageUpload.tsx              →   apps/dashboard/components/ImageUpload.tsx
```

### Documentation
```
Source: Sentinel-Scope/                  Destination: SiteSentinel-AI/
└── INTEGRATION_README.md            →   docs/VISION_INTEGRATION.md
```

## 🔧 Pre-Transfer Checklist

- [ ] Backup SiteSentinel-AI repository
- [ ] Create new branch: `feature/scope-vision-integration`
- [ ] Ensure PostgreSQL database access
- [ ] Verify DeepSeek API key availability
- [ ] Review existing agent architecture in SiteSentinel-AI

## 📝 Transfer Steps

### Step 1: Clone Both Repositories

```bash
# Clone SiteSentinel-AI if not already cloned
git clone https://github.com/NickAiNYC/SiteSentinel-AI
cd SiteSentinel-AI

# Create feature branch
git checkout -b feature/scope-vision-integration

# Create a temporary directory for Sentinel-Scope files
mkdir -p /tmp/scope-transfer
cd /tmp/scope-transfer
git clone https://github.com/NickAiNYC/Sentinel-Scope
```

### Step 2: Copy Backend Files

```bash
# From SiteSentinel-AI root directory
cd /path/to/SiteSentinel-AI

# Create directories if they don't exist
mkdir -p services/agents
mkdir -p services/orchestrator
mkdir -p api/v1
mkdir -p migrations
mkdir -p tests

# Copy agent files
cp /tmp/scope-transfer/Sentinel-Scope/services/agents/__init__.py services/agents/
cp /tmp/scope-transfer/Sentinel-Scope/services/agents/base_agent.py services/agents/
cp /tmp/scope-transfer/Sentinel-Scope/services/agents/visual_scout.py services/agents/
cp /tmp/scope-transfer/Sentinel-Scope/services/agents/guard_agent.py services/agents/

# Copy orchestrator files
cp /tmp/scope-transfer/Sentinel-Scope/services/orchestrator/__init__.py services/orchestrator/
cp /tmp/scope-transfer/Sentinel-Scope/services/orchestrator/graph.py services/orchestrator/

# Copy API routes
cp /tmp/scope-transfer/Sentinel-Scope/api/v1/evidence_routes.py api/v1/

# Copy migration
cp /tmp/scope-transfer/Sentinel-Scope/migrations/003_add_site_evidence.sql migrations/

# Copy tests
cp /tmp/scope-transfer/Sentinel-Scope/tests/test_vision_integration.py tests/
```

### Step 3: Copy Frontend Files

```bash
# Create frontend directories
mkdir -p apps/dashboard/components

# Copy React components
cp /tmp/scope-transfer/Sentinel-Scope/apps/dashboard/components/AgentTheater.tsx apps/dashboard/components/
cp /tmp/scope-transfer/Sentinel-Scope/apps/dashboard/components/ImageUpload.tsx apps/dashboard/components/
```

### Step 4: Copy Documentation

```bash
# Copy integration docs
mkdir -p docs
cp /tmp/scope-transfer/Sentinel-Scope/INTEGRATION_README.md docs/VISION_INTEGRATION.md
```

## 🔄 Integration Steps

### Step 5: Update Dependencies

```bash
# Python dependencies (add to requirements.txt or pyproject.toml)
cat << EOF >> requirements.txt
httpx>=0.27.0
langgraph>=0.2.0
anthropic>=0.75.0
instructor>=1.0.0
rapidfuzz>=3.14.0
EOF

# Install dependencies
pip install -r requirements.txt

# Frontend dependencies (if using npm)
npm install react  # Likely already installed
```

### Step 6: Environment Configuration

```bash
# Add to .env file
cat << 'EOF' >> .env
# DeepSeek Vision API
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/sitesentinel
DEFAULT_ORG_ID=00000000-0000-0000-0000-000000000001

# S3/Cloudinary (optional for image storage)
AWS_S3_BUCKET=site-evidence-uploads
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# or Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
EOF
```

### Step 7: Run Database Migration

```bash
# Connect to PostgreSQL
psql -U postgres -d sitesentinel

# Or use the migration script
psql -U postgres -d sitesentinel -f migrations/003_add_site_evidence.sql

# Verify migration
psql -U postgres -d sitesentinel -c "\d site_evidence"
psql -U postgres -d sitesentinel -c "\dp site_evidence"  # Check RLS policies
```

### Step 8: Update Main Application

If SiteSentinel-AI has a main app.py or similar, update it to include the new routes:

```python
# app.py or main.py
from api.v1.evidence_routes import router as evidence_router

app.include_router(evidence_router)
```

### Step 9: Update Frontend App

If there's a main dashboard app, import and use the AgentTheater:

```typescript
// apps/dashboard/Dashboard.tsx or similar
import { AgentTheater } from './components/AgentTheater';

function Dashboard() {
  return (
    <div>
      <h1>Site Compliance Dashboard</h1>
      <AgentTheater
        siteId={currentSiteId}
        orgId={currentOrgId}
        onAnalysisComplete={(result) => {
          console.log('Analysis complete:', result);
        }}
      />
    </div>
  );
}
```

## ✅ Validation Steps

### Step 10: Run Tests

```bash
# Run vision integration tests
python -m pytest tests/test_vision_integration.py -v

# Expected: 7/11 tests passing initially
# Fix async mock issues for 100% coverage

# Run full test suite
python -m pytest tests/ -v
```

### Step 11: Manual Testing

```bash
# 1. Start the backend
uvicorn app:app --reload --port 8000

# 2. Test health endpoint
curl http://localhost:8000/health

# 3. Test evidence upload (with test image)
curl -X POST http://localhost:8000/api/sites/test-site-id/upload-evidence \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test_image.jpg"

# 4. Check response
# Should return: evidence_id, sha256_hash, analysis results
```

### Step 12: Frontend Testing

```bash
# Start frontend dev server
npm run dev

# Navigate to dashboard
# Open http://localhost:3000/dashboard

# Test:
# 1. Image upload (drag & drop)
# 2. Agent Theater animation
# 3. Vision findings display
# 4. Graceful degradation (skip vision button)
```

## 🔍 Verification Checklist

After transfer, verify:

- [ ] All files copied successfully
- [ ] Dependencies installed
- [ ] Database migration applied
- [ ] RLS policies active
- [ ] Environment variables set
- [ ] Tests run (at least 7/11 passing)
- [ ] API endpoints respond
- [ ] Frontend components render
- [ ] Vision analysis works with DeepSeek API
- [ ] Guard agent validates findings
- [ ] Full pipeline completes (visual_scout → guard → fixer → proof)
- [ ] SHA-256 proof generation works
- [ ] Multi-tenancy (RLS) enforced

## 🐛 Troubleshooting

### Import Errors

```bash
# If you get "ModuleNotFoundError"
# Make sure __init__.py exists in all directories:
touch services/__init__.py
touch services/agents/__init__.py
touch services/orchestrator/__init__.py
touch api/__init__.py
touch api/v1/__init__.py
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d sitesentinel -c "SELECT 1"

# Check RLS is enabled
psql -U postgres -d sitesentinel -c "
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname = 'site_evidence';
"
```

### DeepSeek API Issues

```bash
# Test API key
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# Should return list of available models
```

### LangGraph Execution Errors

```python
# If LangGraph fails, test individual agents first:
from services.agents import VisualScoutAgent

agent = VisualScoutAgent()
result = await agent.run({
    "site_id": "test",
    "org_id": "test",
    "image_url": None  # Test graceful degradation
})
print(result)
```

## 📊 Post-Integration Metrics

Track these metrics after integration:

1. **Vision Analysis Success Rate**: Target >95%
2. **Average API Latency**: Target <2s per image
3. **Guard Failure Rate**: Target <5%
4. **Pipeline Completion Rate**: Target >95%
5. **Cost per Analysis**: Target <$0.002
6. **Test Coverage**: Target >90%

## 🚀 Next Steps After Transfer

1. **Code Review**: Get team review of integration
2. **Security Audit**: Run CodeQL and penetration testing
3. **Performance Testing**: Load test with 100 concurrent uploads
4. **Documentation**: Update main README with vision features
5. **Training**: Train team on new vision capabilities
6. **Rollout Plan**: Gradual rollout to production
   - Week 1: Internal testing
   - Week 2: Beta users (10 sites)
   - Week 3: General availability

## 📞 Support

For issues during transfer:
- **Technical**: Check test_vision_integration.py for examples
- **Documentation**: See VISION_INTEGRATION.md
- **Architecture**: Review services/orchestrator/graph.py

## ✨ Success Criteria

Integration is successful when:
- ✅ All 11 tests pass
- ✅ Vision analysis works end-to-end
- ✅ RLS policies enforce multi-tenancy
- ✅ Frontend displays findings correctly
- ✅ SHA-256 proofs generated
- ✅ Economics validated ($0.0019/analysis)
- ✅ No breaking changes to existing LL149/152 logic
- ✅ Graceful degradation works (skip vision)

---

**Last Updated**: 2026-02-17  
**Version**: 1.0  
**Author**: GitHub Copilot SWE Agent
