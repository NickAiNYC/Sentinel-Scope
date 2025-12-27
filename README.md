# SentinelScope

**LLM Agent for NYC Construction Compliance**

Classifies construction bids/OpenSpace captures → detects compliance gaps → generates proof tables → pulls live DOB alerts for risk context.

## 🎯 Problem
NYC general contractors face "fire drills" during insurance renewals and DOB inspections—scrambling to prove milestone completion from thousands of unstructured OpenSpace captures.

## ✨ Solution
SentinelScope automates evidence indexing:
1. **Classification**: LLM tags captures by milestone, MEP system, location
2. **Gap Detection**: Compares against required compliance milestones
3. **Proof Library**: Generates broker-ready evidence tables
4. **Risk Radar**: Pulls live NYC DOB violation alerts within project radius

## 🚀 Quick Start
\`\`\`bash
git clone https://github.com/NickAiNYC/sentinel-scope
cd sentinel-scope
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## 🛠️ Architecture
\`\`\`
User Upload → LLM Classification → Gap Detection → Report Generation → DOB Risk Alert
      ↓              ↓                 ↓               ↓                 ↓
OpenSpace CSV → milestone tags → compliance gaps → PDF/HTML table → NYC Open Data API
\`\`\`

## 🔧 Tech Stack
- Python, FastAPI/Streamlit
- Anthropic Claude API / DeepSeek API
- NYC Open Data API (Socrata) for DOB violations
- ReportLab/PDF generation

## 📊 Sample Output
| Date | Location | Milestone | Evidence Link | Gap? | Confidence |
|------|----------|-----------|---------------|------|------------|
| 2025-01-15 | Floor 5 | MEP Rough-in | openspace.com/capture123 | No | 95% |
| 2025-01-10 | Floor 4 | Fireproofing | openspace.com/capture456 | Yes | 87% |

## 🚧 Roadmap
- [ ] MVP: Classification + gap detection
- [ ] Streamlit dashboard
- [ ] DOB API integration
- [ ] PDF export
- [ ] OpenSpace API integration

## 📫 Contact
Nick Altstein · NYC · [thrivai.ai](https://thrivai.ai)

## 🎥 Demo
![SentinelScope Demo](demo.gif)

## 🌐 Live Demo
Deploying to Streamlit Cloud...

