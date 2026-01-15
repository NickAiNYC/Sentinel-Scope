# 🏗️ Scope: AI-Powered Construction Compliance Auditor

> **AI Agent for General Contractors - Automated NYC Construction Site Audits & DOB Compliance**

## 🎯 Built for General Contractors

Scope automates construction site compliance auditing specifically for NYC general contractors. It uses computer vision to analyze site photos and cross-references them with NYC Building Code requirements and live DOB violation data for construction sites.

### 🚀 Contractor-Specific Features

- **AI Site Photo Analysis**: Processes construction site imagery to identify milestones
- **NYC DOB Violation Check**: Real-time violation tracking for construction sites
- **Compliance Gap Detection**: Identifies missing construction milestones against NYC BC 2022
- **Forensic Evidence Logs**: Generates audit-ready reports for insurance renewals
- **Permit Monitoring**: Tracks active permits and expiration dates
- **Progress Documentation**: Automates progress tracking for client reporting

## 📊 Contractor Workflow

| Task | Manual Process | With Scope |
|------|----------------|------------|
| **Site Audit** | 40-80 hours manual review | **< 10 minutes** automated analysis |
| **DOB Violation Check** | Manual API queries | **Automated real-time sync** |
| **Insurance Documentation** | Manual compilation | **AI-generated forensic PDF** |
| **Progress Reporting** | Spreadsheet updates | **Automated milestone tracking** |

## 🏗️ Contractor Use Cases

1. **Insurance Renewals**: Automated documentation for carrier requirements
2. **DOB Inspections**: Pre-inspection compliance checks
3. **Client Reporting**: Automated progress updates for owners
4. **Change Order Validation**: Evidence collection for scope changes
5. **Safety Compliance**: Automated safety protocol verification

## 🛠️ Technology Stack

- **AI/ML**: DeepSeek-V3 Vision for construction image analysis
- **NYC Data**: DOB violation API, permit databases, building codes
- **Backend**: Python, Streamlit for rapid deployment
- **Reporting**: Forensic PDF generation for legal/insurance use
- **Geospatial**: BBL-based site identification and mapping

## 🚀 Quick Start for Contractors

### Prerequisites
- Python 3.12+
- DeepSeek API key (for AI image analysis)
- Construction site photos (JPEG/PNG format)

### Installation
```bash
# Clone the repository
git clone https://github.com/NickAiNYC/Scope.git
cd Scope

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env with your DeepSeek API key
```

### Running the Application
```bash
# Start the construction audit dashboard
streamlit run app.py
```

## 📁 Project Structure for Contractors

```
Scope/
├── app.py              # Main contractor dashboard
├── core/               # Construction AI engine
│   ├── gap_detector.py # Compliance gap detection
│   ├── processor.py    # Image batch processing
│   └── geocoding.py    # Site location services
├── violations/         # DOB violation checking
│   └── dob/           # Construction site violation monitoring
├── data/              # Sample construction data
├── tests/             # Construction-specific tests
└── requirements.txt   # Dependencies
```

## 🔧 Contractor API Integration

### Check Construction Site Violations
```python
from violations.dob.dob_engine import DOBEngine

# Check violations for a construction site BBL
violations = DOBEngine.fetch_live_dob_alerts({"bbl": "1012650001"})
print(f"Found {len(violations)} violations at site")
```

### Analyze Construction Progress
```python
from core.gap_detector import ComplianceGapEngine

# Check for missing construction milestones
engine = ComplianceGapEngine(project_type="structural")
found_milestones = ["Foundation", "Structural Steel"]
gap_analysis = engine.detect_gaps(found_milestones)
print(f"Compliance: {gap_analysis.compliance_score}%")
```

## 📊 Contractor Workflow Example

1. **Upload Site Photos** from daily site documentation
2. **AI Identifies** construction milestones and progress
3. **DOB Check** verifies no active violations at site
4. **Gap Analysis** compares against NYC BC 2022 requirements
5. **Generate Report** for insurance or client delivery

## 🏛️ NYC Construction Compliance Coverage

- **NYC Building Code 2022** (BC 2022) - Structural requirements
- **DOB Violation Monitoring** - Site-specific violation checks
- **Permit Compliance** - Active permit tracking
- **Site Safety** - Chapter 33 compliance
- **Special Inspections** - Required inspection tracking

## 👷‍♂️ Related Project: ViolationSentinel

For **landlords and property managers** needing comprehensive property violation monitoring (HPD, 311, DOB across portfolios), see our sister project:

**[ViolationSentinel](https://github.com/NickAiNYC/ViolationSentinel)** - Property management violation dashboard

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NYC DOB** for construction code and violation data
- **DeepSeek** for affordable construction image analysis
- **NYC General Contractors** for workflow validation

---

*Scope is maintained for the NYC construction community.*
*Built by contractors, for contractors.*
