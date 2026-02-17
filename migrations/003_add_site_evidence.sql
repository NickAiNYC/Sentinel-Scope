-- Migration: Add site_evidence table for Scope Vision integration
-- Purpose: Store construction site imagery analysis with multi-tenant RLS
-- Created: 2026-02-17

-- ============================================================================
-- SITE EVIDENCE TABLE
-- ============================================================================
-- Stores visual evidence from construction sites with AI analysis results.
-- Implements Row-Level Security for multi-tenant isolation.

CREATE TABLE IF NOT EXISTS site_evidence (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    site_id UUID NOT NULL,
    -- Note: Assumes 'sites' table exists. Add FK constraint if available:
    -- REFERENCES sites(id) ON DELETE CASCADE,
    
    -- Multi-tenancy (CRITICAL for RLS)
    org_id UUID NOT NULL,
    -- Note: Assumes 'organizations' table exists. Add FK if available:
    -- REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Evidence storage
    image_url TEXT NOT NULL,
    -- URL to S3/Cloudinary stored image
    
    analysis_json JSONB,
    -- Structured findings from VisualScoutAgent:
    -- {
    --   "milestones": ["Foundation", "MEP Rough-in"],
    --   "violations": ["BC §3314.1: Missing fall protection"],
    --   "confidence_score": 0.85,
    --   "agent_source": "VisualScout"
    -- }
    
    -- Audit trail (SHA-256 for tamper-proof evidence chain)
    sha256_hash TEXT UNIQUE,
    -- Hash of original image for forensic verification
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookups by site
CREATE INDEX idx_site_evidence_site_id ON site_evidence(site_id);

-- Fast lookups by organization (for RLS queries)
CREATE INDEX idx_site_evidence_org_id ON site_evidence(org_id);

-- Unique evidence verification
CREATE INDEX idx_site_evidence_sha256 ON site_evidence(sha256_hash);

-- Timestamp-based queries (latest evidence)
CREATE INDEX idx_site_evidence_created_at ON site_evidence(created_at DESC);

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS)
-- ============================================================================
-- Implements "Founding Engineer" multi-tenancy standard.
-- Each organization can ONLY access their own site evidence.

-- Enable RLS on the table
ALTER TABLE site_evidence ENABLE ROW LEVEL SECURITY;

-- Policy: Tenant Isolation
-- Users can only SELECT/INSERT/UPDATE/DELETE evidence for their org
CREATE POLICY tenant_isolation_policy ON site_evidence
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Policy: INSERT requires org_id match
CREATE POLICY tenant_isolation_insert ON site_evidence
    FOR INSERT
    WITH CHECK (org_id = current_setting('app.current_org_id')::uuid);

-- ============================================================================
-- TRIGGER: Auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_site_evidence_updated_at
    BEFORE UPDATE ON site_evidence
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE site_evidence IS 'Visual evidence from construction sites analyzed by VisualScoutAgent';
COMMENT ON COLUMN site_evidence.org_id IS 'Organization ID for RLS multi-tenancy isolation';
COMMENT ON COLUMN site_evidence.sha256_hash IS 'SHA-256 hash of original image for tamper-proof audit trail';
COMMENT ON COLUMN site_evidence.analysis_json IS 'Structured findings from DeepSeek-V3 vision analysis';

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Test that RLS is working (run as different org_id users):
-- 
-- SET app.current_org_id = '00000000-0000-0000-0000-000000000001';
-- SELECT COUNT(*) FROM site_evidence; -- Should only see org 1's data
-- 
-- SET app.current_org_id = '00000000-0000-0000-0000-000000000002';
-- SELECT COUNT(*) FROM site_evidence; -- Should only see org 2's data
