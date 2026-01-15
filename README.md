# 🏗️ Scope: AI-Powered NYC Construction Compliance Auditor

> **Open Source AI Agent for Automated Construction Site Audits & NYC DOB Violation Detection**

## 🎯 What is Scope?

Scope is an open-source AI agent that automates construction site compliance auditing for NYC projects. It uses computer vision to analyze site photos and cross-references them with NYC Building Code requirements and live DOB violation data.

### 🚀 Key Features

- **AI Visual Analysis**: Processes construction site imagery using DeepSeek-V3 Vision
- **NYC DOB Integration**: Real-time violation tracking via NYC Open Data API
- **Compliance Gap Detection**: Identifies missing milestones against NYC BC 2022
- **Forensic Reporting**: Generates audit-ready evidence logs for insurance and inspections
- **Geospatial Intelligence**: BBL-based property lookup and violation mapping

## 📊 Why Use Scope?

| Task | Manual Process | With Scope |
|------|----------------|------------|
| **Site Audit** | 40-80 hours | **< 10 minutes** |
| **Violation Check** | Manual API queries | **Automated real-time sync** |
| **Report Generation** | Manual compilation | **AI-generated forensic PDF** |
| **Compliance Tracking** | Spreadsheet management | **Automated gap detection** |

## 🏗️ Use Cases

1. **General Contractors**: Automated progress documentation for insurance renewals
2. **Project Managers**: Real-time compliance monitoring across multiple sites
3. **Risk Assessors**: Forensic evidence collection for claims and audits
4. **Developers**: Integration with construction management platforms

## 🛠️ Technology Stack

- **AI/ML**: DeepSeek-V3 Vision, OpenAI-compatible API
- **Backend**: Python, Streamlit, FastAPI
- **Data**: NYC Open Data (Socrata API), Geopy for geocoding
- **Reporting**: FPDF2 for forensic PDF generation
- **Frontend**: Streamlit (web interface), React (optional dashboard)

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- DeepSeek API key (or compatible OpenAI API key)
- NYC Open Data App Token (optional, for higher rate limits)

### Installation
```bash
# Clone the repository
git clone https://github.com/NickAiNYC/Scope.git
cd Scope

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application
```bash
# Start the Streamlit web app
streamlit run app.py
```

## 📁 Project Structure

```
Scope/
├── app.py              # Main Streamlit application
├── core/               # Core AI engine modules
├── violations/         # NYC DOB violation management
│   ├── dob/           # DOB API integration
│   ├── reports/       # Report generation
│   └── api/           # REST API endpoints
├── data/              # Mock data and examples
├── tests/             # Test suite
└── requirements.txt   # Python dependencies
```

## 🔧 API Integration

### NYC DOB Violation API
```python
from violations.dob.dob_engine import DOBEngine

# Fetch violations by BBL (Borough-Block-Lot)
violations = DOBEngine.fetch_live_dob_alerts({"bbl": "1012650001"})
```

### Compliance Gap Detection
```python
from core.gap_detector import ComplianceGapEngine

engine = ComplianceGapEngine(project_type="structural")
gap_analysis = engine.detect_gaps(["Foundation", "Structural Steel"])
```

## 📊 Sample Workflow

1. **Upload Site Photos** through the web interface
2. **AI Analysis** identifies construction milestones
3. **DOB Check** fetches live violation data for the property
4. **Gap Detection** compares against NYC BC 2022 requirements
5. **Report Generation** creates forensic evidence PDF

## 🏛️ NYC Compliance Coverage

- **NYC Building Code 2022** (BC 2022)
- **NYC Existing Building Code** (EBC 2025)
- **DOB Violation Classes** (A, B, C)
- **Local Law 97** Carbon Compliance
- **1 RCNY 103-15** Parapet Inspection Rules

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
ruff check . --fix
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NYC Open Data** for providing public access to DOB records
- **DeepSeek** for affordable AI vision capabilities
- **Streamlit** for rapid web application development

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/NickAiNYC/Scope/issues)
- **Documentation**: [Project Wiki](https://github.com/NickAiNYC/Scope/wiki)
- **Email**: Contact through GitHub profile

---

*Scope is maintained by [NickAiNYC](https://github.com/NickAiNYC).*
*This project is for educational and demonstration purposes.*
