# 🛡️ SentinelScope
### **AI-Augmented Forensic Audit Agent for NYC Construction Compliance**

> **Automating the bridge between construction site reality and NYC Building Code compliance.**

---

## 🎯 The Problem
General Contractors in NYC waste **40-80 hours per project** manually searching through unstructured photo logs to prove milestone completion for insurance renewals and DOB inspections.

* **Manual Effort:** ~$5k labor cost per review cycle.
* **Risk:** Human error leads to missed compliance gaps and insurance friction.

---

## 🚀 The Solution
SentinelScope leverages **DeepSeek-V3 Vision** and **NYC Open Data** to provide a real-time, forensic-grade audit of construction progress.

### Core Features
* **Parallel Vision Audit:** Processes batches of site captures simultaneously.
* **NYC DOB Live Sync:** Real-time violation tracking via BBL geocoding.
* **Forensic PDF Export:** Generates audit-ready evidence logs for risk adjusters.
* **Gap Detection:** Compares site imagery against **NYC BC 2022** requirements.

---

## 📊 Business Impact

| Metric | Manual Process | With SentinelScope |
| :--- | :--- | :--- |
| **Audit Time** | 40 - 80 Hours | **< 10 Minutes** |
| **Cost** | $5,000+ | **<$1.50 (API fees)** |
| **Data Integrity** | Subjective | **AI-Verified Forensic Log** |

---

## 🛠️ Tech Stack
* **AI Brain:** DeepSeek-V3 Vision (OpenAI SDK compatible)
* **Data Engine:** Pandas, Geopy (BBL Geocoding), NYC Socrata API
* **Reporting:** FPDF2 (Forensic PDF Generation)
* **UI:** Streamlit (Custom Professional Theme)

---

## 🚦 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone [https://github.com/NickAiNYC/sentinel-scope.git](https://github.com/NickAiNYC/sentinel-scope.git)
cd sentinel-scope

# Install dependencies
pip install -r requirements.txt
