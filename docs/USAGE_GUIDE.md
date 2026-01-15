# 📖 Usage Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Managing Projects](#managing-projects)
- [Running Audits](#running-audits)
- [Understanding Results](#understanding-results)
- [Exporting Reports](#exporting-reports)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
Before using SentinelScope, ensure you have:
- ✅ Python 3.10+ installed
- ✅ DeepSeek API key ([get one here](https://platform.deepseek.com))
- ✅ Supabase account ([sign up here](https://supabase.com))
- ✅ NYC construction site photos (JPG/PNG format)

### Installation

#### Option 1: Use the Live Demo
Visit [sentinelscope.streamlit.app](https://sentinelscope.streamlit.app) - no installation needed!

#### Option 2: Run Locally
```bash
# Clone the repository
git clone https://github.com/NickAiNYC/Sentinel-Scope.git
cd Sentinel-Scope

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Configure Streamlit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your credentials

# Run the application
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

---

## Managing Projects

### Creating Your First Project

1. **Navigate to the Dashboard**
   - After logging in, you'll see the portfolio dashboard
   - Click **"New Project Audit"** in the sidebar

2. **Enter Project Details**
   - **Project Name:** e.g., "123 Main Street Renovation"
   - **Address:** Full NYC address for DOB data integration
   - **Project Type:** Select from:
     - Commercial (office buildings, retail)
     - Residential (single/multi-family homes)
     - Industrial (warehouses, manufacturing)
     - Institutional (schools, hospitals)
   - **Start Date:** When construction began
   - **Expected Completion:** Projected finish date

3. **Save the Project**
   - Click **"Create Project"**
   - The project appears in your portfolio dashboard

### Viewing All Projects

The **Portfolio Dashboard** shows:
- **Project Cards:** Quick overview of each active project
- **Compliance Scores:** Overall percentage by project
- **Risk Indicators:** Color-coded alerts (Green/Yellow/Red)
- **Last Audit Date:** When the project was last reviewed
- **Quick Actions:** Edit, Archive, or Delete projects

### Editing Project Details

1. Click on a project card in the dashboard
2. Select **"Edit Project"** from the actions menu
3. Update any fields (name, address, dates)
4. Click **"Save Changes"**

### Archiving Completed Projects

1. Navigate to the project details page
2. Click **"Archive Project"**
3. Archived projects are hidden from the main dashboard but remain in the database

---

## Running Audits

### Preparing Your Photos

**Best Practices for Site Captures:**

✅ **DO:**
- Take clear, well-lit photos during daylight
- Capture multiple angles of each construction phase
- Include close-ups of critical systems (foundation, MEP, fireproofing)
- Take wide shots showing overall progress
- Ensure photos are recent (ideally within 1-2 weeks)
- Use landscape orientation for better context

❌ **DON'T:**
- Upload blurry or dark photos
- Submit photos of plans/drawings instead of actual site
- Include photos with people blocking important features
- Use photos from other projects (contaminate the audit)

**Recommended Photo Count:**
- **Minimum:** 10-15 photos (basic coverage)
- **Standard:** 30-50 photos (comprehensive audit)
- **Detailed:** 100+ photos (forensic analysis)

### Starting a New Audit

1. **Select a Project**
   - From the dashboard, click the project you want to audit
   - Or create a new project (see above)

2. **Upload Photos**
   ```
   Method 1: Drag and Drop
   - Drag photo files directly into the upload area
   - Supports batch upload of multiple files
   
   Method 2: File Browser
   - Click "Browse Files"
   - Select photos from your computer (Cmd/Ctrl+Click for multiple)
   - Click "Open"
   ```

3. **Configure Audit Settings**
   - **Audit Focus:** Select systems to prioritize:
     - Structural (foundation, framing, concrete)
     - MEP (mechanical, electrical, plumbing)
     - Life Safety (egress, fire protection, sprinklers)
     - Envelope (exterior walls, windows, weatherproofing)
   - **Strictness Level:**
     - Conservative: Flag all potential gaps
     - Balanced: Flag likely gaps (recommended)
     - Lenient: Flag only clear violations

4. **Run the Analysis**
   - Click **"Analyze Photos"**
   - Processing time: ~2-3 seconds per image
   - Progress bar shows real-time status
   - You can cancel anytime if needed

### Batch Processing Mode

For large audits (50+ photos), use batch mode for 60% faster processing:

1. Enable **"Batch Processing"** in settings
2. Upload all photos at once
3. The system groups images and makes optimized API calls
4. Results appear after all images are processed

**Cost Savings:**
- Individual mode: $0.00027 per gap × 5 gaps = $0.00135
- Batch mode: $0.00055 total for 5 gaps
- Savings: 59% reduction in API costs

---

## Understanding Results

### Compliance Score

The **overall compliance score** (0-100%) represents:
- **100%:** All required milestones detected, no gaps
- **75-99%:** Minor gaps identified
- **50-74%:** Moderate compliance issues
- **Below 50%:** Major gaps requiring immediate attention

**How It's Calculated:**
```
Score = (Detected Milestones / Total Required Milestones) × 100
```

For example:
- Project type: Commercial
- Required milestones: 15
- Detected milestones: 12
- **Compliance Score: 80%**

### Gap Analysis Table

Each compliance gap shows:

| Field | Description | Example |
|-------|-------------|---------|
| **Gap ID** | Unique identifier | GAP-001 |
| **System** | Construction category | Structural |
| **Missing Milestone** | What's not documented | Foundation Inspection |
| **Risk Level** | Severity (Critical/High/Medium/Low) | HIGH |
| **NYC Code Reference** | Relevant building code section | BC 1704.4 |
| **Remediation** | Suggested action | Schedule DOB inspection within 7 days |

### Risk Levels Explained

**🔴 CRITICAL**
- Missing inspections that could halt work
- Life safety system gaps (egress, fire protection)
- **Action:** Address immediately (within 24 hours)

**🟠 HIGH**
- Structural documentation gaps
- MEP system deficiencies
- **Action:** Resolve within 1 week

**🟡 MEDIUM**
- Minor compliance items
- Documentation formatting issues
- **Action:** Address within 2 weeks

**🟢 LOW**
- Non-critical gaps
- Optional enhancements
- **Action:** Track for future audits

### Visual Evidence

For each detected milestone, the system shows:
- **Matched Photo:** Which image contained the evidence
- **Confidence Score:** AI certainty (0-100%)
- **Visual Markers:** Specific architectural features detected
- **NYC Code Mapping:** Relevant building code sections

**Confidence Interpretation:**
- **90-100%:** High confidence, AI is very certain
- **70-89%:** Medium confidence, likely correct
- **Below 70%:** Low confidence, review manually

### NYC DOB Violations

If you provided a valid NYC address, the system pulls:
- **Open Violations:** Active DOB complaints
- **ECB Violations:** Environmental Control Board citations
- **DOB Complaints:** Public complaints filed
- **Inspection History:** Past DOB visits

This data is updated in real-time from the NYC Open Data API.

---

## Exporting Reports

### PDF Export

Generate an audit-ready PDF report:

1. Click **"Export PDF"** button
2. The report includes:
   - Executive summary with compliance score
   - Gap analysis table with risk levels
   - Visual evidence photos (thumbnails)
   - NYC code references
   - Recommendations for remediation
   - Legal timestamp

3. PDF is automatically downloaded to your computer
4. File naming: `SentinelScope_Audit_[ProjectName]_[Date].pdf`

**Use Cases:**
- Insurance audits
- Internal compliance reviews
- Stakeholder presentations
- Legal documentation

### JSON Export

Export structured data for integrations:

1. Click **"Export JSON"**
2. The file contains:
   - Project metadata
   - All detected milestones (with confidence scores)
   - Complete gap analysis
   - NYC DOB violation data
   - Audit timestamp and AI model version

3. JSON structure:
   ```json
   {
     "project": {...},
     "audit": {...},
     "gaps": [...],
     "milestones": [...],
     "dob_data": {...}
   }
   ```

**Use Cases:**
- Procore integration
- Autodesk BIM 360 sync
- Custom analytics dashboards
- API consumption by other tools

### CSV Export

Export tabular data for spreadsheet analysis:

1. Click **"Export CSV"**
2. Generates three CSV files:
   - `gaps.csv`: All compliance gaps
   - `milestones.csv`: Detected milestones
   - `dob_violations.csv`: NYC DOB data

3. Open in Excel, Google Sheets, or import into databases

**Use Cases:**
- Financial analysis
- Portfolio-wide reporting
- Custom visualizations
- Historical trend tracking

---

## Best Practices

### Photography Tips

1. **Lighting**
   - Shoot during golden hour (early morning/late afternoon)
   - Avoid harsh shadows and direct overhead sun
   - Use flash for dark interior spaces

2. **Composition**
   - Include reference objects for scale (tape measure, person)
   - Capture wide context shots before close-ups
   - Take photos from multiple angles (0°, 45°, 90°)

3. **Documentation**
   - Name photo files with dates and locations (e.g., `Foundation_2025-01-15.jpg`)
   - Take photos before and after each construction phase
   - Document any corrections or remediation work

### Audit Frequency

**Recommended Schedule:**

| Project Phase | Audit Frequency | Reason |
|---------------|-----------------|--------|
| **Pre-construction** | Once | Baseline documentation |
| **Foundation/Structure** | Weekly | High-risk phase, frequent inspections |
| **MEP Rough-in** | Bi-weekly | Complex systems, many code requirements |
| **Closeout/Final** | Once | Insurance audit preparation |

**Insurance Renewal Cycle:**
- Run comprehensive audit 2-4 weeks before renewal
- Allows time to remediate any gaps discovered
- Reduces premium risk from incomplete documentation

### Data Management

1. **Project Naming Convention**
   - Use consistent format: `[Address] - [Type] - [Year]`
   - Example: `123 Main St - Commercial - 2025`

2. **Photo Organization**
   - Create folders by construction phase
   - Use subfolders by system (Structural, MEP, etc.)
   - Archive photos after audit completion

3. **Report Storage**
   - Save all exported reports (PDF, JSON, CSV)
   - Organize by project and date
   - Keep for 7+ years for legal compliance

### Collaboration

1. **Team Access**
   - Invite team members with appropriate roles:
     - **Admin:** Full access, can delete projects
     - **Editor:** Can create/edit projects and audits
     - **Viewer:** Read-only access to reports

2. **Communication**
   - Use the built-in comment system to annotate gaps
   - Tag team members with `@username` for notifications
   - Export reports to share with external stakeholders

---

## Troubleshooting

### Common Issues

#### "API Key Invalid" Error
**Solution:**
1. Verify your DeepSeek API key at https://platform.deepseek.com
2. Check `.streamlit/secrets.toml` for typos
3. Ensure no extra spaces or quotes in the key
4. Generate a new API key if needed

#### Photos Not Uploading
**Solution:**
1. Check file format (only JPG, PNG supported)
2. Verify file size (max 10MB per image)
3. Try uploading fewer images at once
4. Clear browser cache and refresh

#### Low Confidence Scores
**Solution:**
1. Re-take photos with better lighting
2. Upload more photos showing different angles
3. Ensure photos are recent and relevant to current phase
4. Manually override AI classification if needed

#### Missing NYC DOB Data
**Solution:**
1. Verify the address is valid and in NYC
2. Check BBL (Borough-Block-Lot) number
3. NYC Open Data API may be temporarily down (retry later)
4. Some addresses may not be in the database

#### Slow Performance
**Solution:**
1. Use batch processing mode for large uploads
2. Resize photos before upload (max 2MB recommended)
3. Check your internet connection
4. Upgrade to a paid API tier for higher rate limits

### Getting Help

If you encounter issues not covered here:
1. Check the [FAQ](FAQ.md) for common questions
2. Search [GitHub Issues](https://github.com/NickAiNYC/Sentinel-Scope/issues)
3. Open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Screenshots (if applicable)
   - Error messages
4. Email support: nick@thrivai.ai

---

## Advanced Features

### AI Compliance Assistant

Ask natural language questions about NYC Building Code:

**Example Queries:**
- "What's required for scaffolding inspections?"
- "Explain my current gaps"
- "When is my next DOB inspection due?"
- "What's the code for fire protection?"

The assistant provides context-aware responses with code citations.

### Custom Milestone Templates

Create your own milestone checklists:

1. Go to **Settings → Milestones**
2. Click **"New Template"**
3. Add custom milestones for your project type
4. Save and apply to future audits

### API Integration

For developers, SentinelScope offers JSON export for custom integrations:

```python
# Example: Load audit data in Python
import json

with open('audit_export.json') as f:
    data = json.load(f)
    
gaps = data['gaps']
for gap in gaps:
    print(f"{gap['system']}: {gap['missing_milestone']}")
```

See [API.md](API.md) for full API documentation.

---

**Need more help?** Check out:
- [FAQ](FAQ.md) - Common questions
- [Technical Architecture](TECHNICAL_ARCHITECTURE.md) - System details
- [Contributing Guide](CONTRIBUTING.md) - Development setup

**Happy auditing! 🏗️**
