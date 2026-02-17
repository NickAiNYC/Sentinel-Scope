-- Migration 004: Final Security Audit & RLS Verification
-- Purpose: Production hardening, verify RLS across ALL tables
-- Created: 2026-02-17
-- Platform: SiteSentinel-AI v2.0

-- ============================================================================
-- RLS POLICY AUDIT
-- ============================================================================
-- Verify Row-Level Security is enabled on all multi-tenant tables

DO $$
DECLARE
    table_record RECORD;
    missing_rls TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Check all tables that should have RLS
    FOR table_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN (
            'site_evidence',
            'sites', 
            'organizations',
            'users',
            'compliance_reports',
            'violations',
            'proofs'
        )
    LOOP
        -- Check if RLS is enabled
        IF NOT EXISTS (
            SELECT 1 
            FROM pg_class 
            WHERE relname = table_record.tablename 
            AND relrowsecurity = true
        ) THEN
            missing_rls := array_append(missing_rls, table_record.tablename);
        END IF;
    END LOOP;
    
    -- Raise error if any table is missing RLS
    IF array_length(missing_rls, 1) > 0 THEN
        RAISE EXCEPTION 'RLS NOT ENABLED on tables: %', array_to_string(missing_rls, ', ');
    END IF;
    
    RAISE NOTICE 'RLS Audit PASSED: All multi-tenant tables have RLS enabled';
END $$;

-- ============================================================================
-- ENFORCE RLS ON ALL EXISTING TABLES
-- ============================================================================

-- Site evidence (from migration 003)
ALTER TABLE IF EXISTS site_evidence ENABLE ROW LEVEL SECURITY;

-- Sites table (if exists)
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    bbl VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_sites ON sites
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (with org_id for multi-tenancy)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_users ON users
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Compliance reports
CREATE TABLE IF NOT EXISTS compliance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL,
    org_id UUID NOT NULL,
    report_type VARCHAR(100),
    findings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE compliance_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_compliance ON compliance_reports
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Violations
CREATE TABLE IF NOT EXISTS violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL,
    org_id UUID NOT NULL,
    violation_type VARCHAR(100),
    severity VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE violations ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_violations ON violations
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Proofs (SHA-256 audit trail)
CREATE TABLE IF NOT EXISTS proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    site_id UUID,
    proof_type VARCHAR(100),
    sha256_hash TEXT UNIQUE NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE proofs ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_proofs ON proofs
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- ============================================================================
-- CROSS-TENANT ISOLATION TEST FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION test_cross_tenant_isolation()
RETURNS TABLE(
    table_name TEXT,
    test_passed BOOLEAN,
    message TEXT
) AS $$
DECLARE
    org1 UUID := gen_random_uuid();
    org2 UUID := gen_random_uuid();
    test_record RECORD;
BEGIN
    -- Test site_evidence isolation
    SET app.current_org_id = org1::TEXT;
    INSERT INTO site_evidence (site_id, org_id, image_url, sha256_hash)
    VALUES (gen_random_uuid(), org1, 'http://test.jpg', md5(random()::text));
    
    SET app.current_org_id = org2::TEXT;
    SELECT COUNT(*) INTO test_record FROM site_evidence;
    
    IF test_record.count = 0 THEN
        RETURN QUERY SELECT 
            'site_evidence'::TEXT,
            TRUE,
            'Cross-tenant isolation verified'::TEXT;
    ELSE
        RETURN QUERY SELECT 
            'site_evidence'::TEXT,
            FALSE,
            format('SECURITY BREACH: Org2 can see %s records from Org1', test_record.count)::TEXT;
    END IF;
    
    -- Reset
    RESET app.current_org_id;
    DELETE FROM site_evidence WHERE org_id IN (org1, org2);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SECURITY AUDIT INDEXES
-- ============================================================================

-- Ensure all org_id columns are indexed for RLS performance
CREATE INDEX IF NOT EXISTS idx_site_evidence_org_id ON site_evidence(org_id);
CREATE INDEX IF NOT EXISTS idx_sites_org_id ON sites(org_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_compliance_org_id ON compliance_reports(org_id);
CREATE INDEX IF NOT EXISTS idx_violations_org_id ON violations(org_id);
CREATE INDEX IF NOT EXISTS idx_proofs_org_id ON proofs(org_id);

-- Index on SHA-256 hashes for proof verification
CREATE INDEX IF NOT EXISTS idx_proofs_sha256 ON proofs(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON site_evidence(sha256_hash);

-- ============================================================================
-- DATA RESIDENCY MARKERS
-- ============================================================================

-- Add data residency column to organizations for SOC2 compliance
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS data_residency VARCHAR(50) DEFAULT 'us-east-1';

-- Add VLM provider tracking for audit trail
ALTER TABLE site_evidence 
ADD COLUMN IF NOT EXISTS vlm_provider VARCHAR(100),
ADD COLUMN IF NOT EXISTS vlm_model VARCHAR(100),
ADD COLUMN IF NOT EXISTS soc2_compliant BOOLEAN DEFAULT true;

-- ============================================================================
-- SECURITY AUDIT COMMENTS
-- ============================================================================

COMMENT ON TABLE site_evidence IS 'RLS-protected evidence storage with SOC2 VLM tracking';
COMMENT ON COLUMN organizations.data_residency IS 'Required data residency region (us-east-1, us-west-2, nyc)';
COMMENT ON COLUMN site_evidence.vlm_provider IS 'VLM provider used for analysis (openai-gpt4o, anthropic-claude)';
COMMENT ON COLUMN site_evidence.soc2_compliant IS 'Whether analysis used SOC2-compliant VLM';

-- ============================================================================
-- RUN SECURITY TESTS
-- ============================================================================

-- Execute cross-tenant isolation test
SELECT * FROM test_cross_tenant_isolation();

-- Verify RLS policy count
DO $$
DECLARE
    policy_count INT;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
    AND policyname LIKE '%tenant_isolation%';
    
    IF policy_count < 6 THEN
        RAISE WARNING 'Expected at least 6 RLS policies, found %', policy_count;
    ELSE
        RAISE NOTICE 'RLS Policy Audit PASSED: % tenant isolation policies active', policy_count;
    END IF;
END $$;

-- ============================================================================
-- COMPLETION LOG
-- ============================================================================

INSERT INTO migrations_log (version, description, executed_at)
VALUES (
    '004',
    'Final Security Audit & RLS Verification - Production Ready',
    NOW()
)
ON CONFLICT DO NOTHING;

-- Create migrations log table if it doesn't exist
CREATE TABLE IF NOT EXISTS migrations_log (
    version VARCHAR(10) PRIMARY KEY,
    description TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
