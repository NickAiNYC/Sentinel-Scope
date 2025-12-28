import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from fpdf import FPDF
from typing import List

# ====== STREAMLIT CLOUD PATH FIX ======
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ====== CORE MODULE IMPORTS ======
try:
    from core.constants import BRAND_THEME
    from core.geocoding import lookup_address
    from core.dob_engine import DOBEngine  # FIXED: Importing the Class
    from core.gap_detector import ComplianceGapEngine
    from core.processor import SentinelBatchProcessor
except ImportError as e:
    st.error(f"Critical Import Error: {e}")
    st.stop()

# ====== PDF GENERATION ENGINE ======
class SentinelReport(FPDF):
    def header(self):
        self.set_fill_color(33, 47, 61)  # Deep Charcoal
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 15, 'SENTINEL-SCOPE AI | CONSTRUCTION FORENSICS', 0, 1, 'L')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'NYC BC 2022 Compliance Verification & Risk Evidence', 0, 1, 'L')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f'Forensic Log ID: {id(self)} | Generated: {timestamp} | Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(p_name, address, analysis, findings: List):
    pdf = SentinelReport()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(139, 69, 19) 
    pdf.cell(0, 10, txt=f"PROJECT: {p_name.upper()}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, txt=f"LOCATION: {address}", ln=True)
    pdf.cell(0, 7, txt=f"COMPLIANCE RATING: {analysis.compliance_score}%", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Milestone", 1, 0, 'C', True)
    pdf.cell(20, 10, "Floor", 1, 0, 'C', True)
    pdf.cell(20, 10, "Conf.", 1, 0, 'C', True)
    pdf.cell(110, 10, "Forensic Evidence Narrative", 1, 1, 'C', True)
    pdf.set_font("Arial", size=8)
    for res in findings:
        pdf.cell(40, 15, str(res.milestone), 1)
        pdf.cell(20, 15, f"FL {res.floor}", 1)
        pdf.cell(20, 15, f"{res.confidence*100:.0f}%", 1)
        pdf.multi_cell(110, 5, res.evidence_notes, 1)
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG & THEME ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; }}
    h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']}; font-weight: 800; }}
    .stButton>button {{ background-color: {BRAND_THEME['SADDLE_BROWN']}; color: white; border-radius: 8px; width: 100%; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=70)
    st.title("SentinelScope AI")
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP", "Fireproofing", "Foundation"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        submit = st.form_submit_button("🚀 INITIALIZE AUDIT")

# --- AUDIT EXECUTION ---
if submit and uploads:
    if not api_key:
        st.error("Missing DEEPSEEK_API_KEY in Streamlit Secrets.")
        st.stop()

    geo_info = lookup_address(address)
    bbl = geo_info.get("bbl", "1012650001")
    
    with st.status("🕵️ Running AI Visual Audit...", expanded=True) as status:
        gap_engine = ComplianceGapEngine(project_type=p_type.lower())
        batch_processor = SentinelBatchProcessor(engine=gap_engine, api_key=api_key)
        
        st.write("🛰️ Pulling NYC DOB Records...")
        # FIXED: Using the DOBEngine class instead of the missing function
        dob_engine = DOBEngine()
        live_violations = dob_engine.get_alerts(bbl) # Update to match your dob_engine method name
        
        st.write("👁️ Analyzing Visual Compliance...")
        raw_findings = [batch_processor._process_single_image(f) for f in uploads]
        
        found_milestones = list(set([f.milestone for f in raw_findings if f.milestone != "Unknown"]))
        analysis = gap_engine.detect_gaps(found_milestones)
        
        st.session_state.audit_results = {
            "analysis": analysis,
            "raw_findings": raw_findings,
            "geo_info": geo_info,
            "live_violations": live_violations,
            "meta": {"name": p_name, "address": address}
        }
        status.update(label="Audit Complete!", state="complete", expanded=False)

# --- DASHBOARD DISPLAY ---
if st.session_state.audit_results:
    res = st.session_state.audit_results
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliance Score", f"{res['analysis'].compliance_score}%")
    c2.metric("Risk Score", res['analysis'].risk_score)
    c3.metric("Detected Milestones", len(set([f.milestone for f in res['raw_findings']])))
    c4.metric("BBL Number", res['geo_info'].get('bbl', 'N/A'))

    tab1, tab2, tab3 = st.tabs(["🏗️ Visual Audit", "🚨 NYC DOB Sync", "🛡️ Evidence Export"])

    with tab1:
        st.header("Spatial Mapping & Progress")
        col_map, col_img = st.columns([1.5, 1])
        with col_map:
            map_data = pd.DataFrame({'lat': [res['geo_info']['lat']], 'lon': [res['geo_info']['lon']]})
            st.map(map_data, zoom=16)
        with col_img:
            st.image(uploads[0], caption="Latest Field Capture", use_container_width=True)
            st.warning(f"**Action Required:** {res['analysis'].next_priority}")

    with tab2:
        st.header("DOB Active Violation Sync")
        if res['live_violations']:
            st.error(f"🚨 FOUND {len(res['live_violations'])} ACTIVE VIOLATIONS")
            st.dataframe(res['live_violations'], use_container_width=True)
        else:
            st.success("✅ No active violations found for this Property Block (BBL).")

    with tab3:
        st.header("Forensic PDF Export")
        pdf_bytes = create_pdf_report(res['meta']['name'], res['meta']['address'], res['analysis'], res['raw_findings'])
        st.download_button(
            label="📄 DOWNLOAD FORENSIC EVIDENCE LOG",
            data=pdf_bytes,
            file_name=f"SentinelReport_{res['meta']['name'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.table(pd.DataFrame([{
            "Milestone": f.milestone, 
            "Floor": f.floor, 
            "Confidence": f"{f.confidence*100:.1f}%", 
            "Notes": f.evidence_notes} for f in res['raw_findings']]))
else:
    st.title("SentinelScope AI Command Center")
    st.info("Ready for Audit. Please upload site imagery via the sidebar to begin.")
