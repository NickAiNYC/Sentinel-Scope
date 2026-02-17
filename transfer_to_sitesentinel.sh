#!/bin/bash
# =============================================================================
# SiteSentinel-AI Integration Transfer Script
# =============================================================================
# Purpose: Transfer Scope vision integration files to SiteSentinel-AI
# Usage: ./transfer_to_sitesentinel.sh /path/to/SiteSentinel-AI
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Source and destination paths
SCOPE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITESENTINEL_ROOT="${1:-}"

# Validate arguments
if [ -z "$SITESENTINEL_ROOT" ]; then
    echo -e "${RED}Error: SiteSentinel-AI path required${NC}"
    echo "Usage: $0 /path/to/SiteSentinel-AI"
    exit 1
fi

if [ ! -d "$SITESENTINEL_ROOT" ]; then
    echo -e "${RED}Error: SiteSentinel-AI directory not found: $SITESENTINEL_ROOT${NC}"
    exit 1
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  SiteSentinel-AI Integration Transfer${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo -e "${YELLOW}Source:${NC}      $SCOPE_ROOT"
echo -e "${YELLOW}Destination:${NC} $SITESENTINEL_ROOT"
echo ""

# Create backup
BACKUP_DIR="$SITESENTINEL_ROOT/.backup-$(date +%Y%m%d-%H%M%S)"
echo -e "${YELLOW}Creating backup:${NC} $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# =============================================================================
# File Transfer Manifest
# =============================================================================

declare -A FILES=(
    # Backend Agents
    ["services/agents/__init__.py"]="services/agents/__init__.py"
    ["services/agents/base_agent.py"]="services/agents/base_agent.py"
    ["services/agents/visual_scout.py"]="services/agents/visual_scout.py"
    ["services/agents/guard_agent.py"]="services/agents/guard_agent.py"
    ["services/agents/vlm_router.py"]="services/agents/vlm_router.py"
    
    # Orchestration
    ["services/orchestrator/__init__.py"]="services/orchestrator/__init__.py"
    ["services/orchestrator/graph.py"]="services/orchestrator/graph.py"
    
    # API Routes
    ["api/v1/evidence_routes.py"]="api/v1/evidence_routes.py"
    
    # Database Migrations
    ["migrations/003_add_site_evidence.sql"]="migrations/003_add_site_evidence.sql"
    ["migrations/004_final_security_audit.sql"]="migrations/004_final_security_audit.sql"
    
    # Frontend Components
    ["apps/dashboard/components/AgentTheater.tsx"]="apps/dashboard/components/AgentTheater.tsx"
    ["apps/dashboard/components/ImageUpload.tsx"]="apps/dashboard/components/ImageUpload.tsx"
    
    # Tests
    ["tests/test_vision_integration.py"]="tests/test_vision_integration.py"
    ["tests/test_rls_compliance.py"]="tests/test_rls_compliance.py"
    
    # Documentation
    ["INTEGRATION_README.md"]="docs/VISION_INTEGRATION.md"
    ["TRANSFER_GUIDE.md"]="docs/TRANSFER_GUIDE.md"
    
    # Configuration
    [".env.example"]=".env.example"
)

# Transfer counter
transferred=0
skipped=0
failed=0

echo ""
echo -e "${BLUE}Transferring files...${NC}"
echo ""

for source in "${!FILES[@]}"; do
    dest="${FILES[$source]}"
    source_path="$SCOPE_ROOT/$source"
    dest_path="$SITESENTINEL_ROOT/$dest"
    
    # Check if source exists
    if [ ! -f "$source_path" ]; then
        echo -e "${RED}✗${NC} $source ${RED}(not found)${NC}"
        ((failed++))
        continue
    fi
    
    # Create destination directory
    dest_dir=$(dirname "$dest_path")
    mkdir -p "$dest_dir"
    
    # Backup existing file if it exists
    if [ -f "$dest_path" ]; then
        backup_path="$BACKUP_DIR/$dest"
        mkdir -p "$(dirname "$backup_path")"
        cp "$dest_path" "$backup_path"
        echo -e "${YELLOW}↻${NC} $dest ${YELLOW}(backed up)${NC}"
    fi
    
    # Copy file
    cp "$source_path" "$dest_path"
    echo -e "${GREEN}✓${NC} $dest"
    ((transferred++))
done

# =============================================================================
# Update .env if it doesn't exist
# =============================================================================

if [ ! -f "$SITESENTINEL_ROOT/.env" ] && [ -f "$SITESENTINEL_ROOT/.env.example" ]; then
    echo ""
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp "$SITESENTINEL_ROOT/.env.example" "$SITESENTINEL_ROOT/.env"
    echo -e "${GREEN}✓${NC} Created .env (remember to add your API keys)"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  Transfer Summary${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo -e "${GREEN}Transferred:${NC} $transferred files"
echo -e "${YELLOW}Skipped:${NC}     $skipped files"
echo -e "${RED}Failed:${NC}      $failed files"
echo ""

if [ $failed -gt 0 ]; then
    echo -e "${RED}⚠ Some files failed to transfer. Check the output above.${NC}"
    exit 1
fi

# =============================================================================
# Post-Transfer Instructions
# =============================================================================

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  Next Steps${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo "1. Update environment variables in .env:"
echo "   - OPENAI_API_KEY (for GPT-4o vision)"
echo "   - ANTHROPIC_API_KEY (for Claude 3.5, optional)"
echo "   - VLM_PROVIDER (default: openai-gpt4o)"
echo "   - DATA_RESIDENCY (default: us-east-1)"
echo ""
echo "2. Install Python dependencies:"
echo "   cd $SITESENTINEL_ROOT"
echo "   pip install httpx langgraph anthropic"
echo ""
echo "3. Run database migrations:"
echo "   psql -U postgres -d sitesentinel -f migrations/003_add_site_evidence.sql"
echo "   psql -U postgres -d sitesentinel -f migrations/004_final_security_audit.sql"
echo ""
echo "4. Run tests to verify:"
echo "   pytest tests/test_vision_integration.py -v"
echo "   pytest tests/test_rls_compliance.py -v"
echo ""
echo "5. Update main app.py to include evidence routes:"
echo "   from api.v1.evidence_routes import router as evidence_router"
echo "   app.include_router(evidence_router)"
echo ""
echo -e "${GREEN}✓ Transfer complete!${NC}"
echo ""
echo -e "${YELLOW}Backup location:${NC} $BACKUP_DIR"
echo ""
