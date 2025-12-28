import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from fpdf import FPDF
from typing import List

# ====== STREAMLIT CLOUD PATH FIX ======
# This resolves the ImportError by adding the root directory to sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ====== CORE MODULE IMPORTS ======
try:
    from core.constants import BRAND_THEME
    from core.geocoding import lookup_address
    from core.dob_engine import fetch_live_dob_alerts
    from core.gap_detector import ComplianceGapEngine
    from core.processor import SentinelBatchProcessor
except ImportError as e:
    st.error(f"Critical Import Error: {e}")
    st.stop()

# ====== PDF GENERATION ENGINE ======
class SentinelReport(FPDF):
    def header(self):
        # Dark Branding Bar
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 30, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SENTINEL-SCOPE AI | CONSTRUCTION EVIDENCE LOG', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Forensic Audit Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def create_pdf_report(p_name, address, analysis, findings: List):
    pdf = SentinelReport()
    pdf.add_page()
    
    # Project Summary Header
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(139, 69, 19) # PRIMARY_BROWN
    pdf.cell(0, 10, txt=f"Project: {p_name}", ln=True)
    
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, txt=f"Site Address: {address}", ln=True)
    pdf.cell(0, 7, txt=f"Final Compliance Score: {analysis.compliance_score}%", ln=True)
    pdf.ln(10)
    
    # Audit Table
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, txt="AI-Verified Evidence Logs (NYC BC 2022)", ln=True)
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(40, 10, "Milestone", 1, 0, 'C', True)
    pdf.cell(25, 10, "Location", 1, 0, 'C', True)
    pdf.cell(25, 10, "Confidence", 1, 0, 'C', True)
    pdf.cell(100, 10, "Forensic Evidence Notes", 1, 1, 'C', True)
    
    # Table Content
    pdf.set_font("Arial", size=8)
    for res in findings:
        # Calculate height needed for the note to keep row borders aligned
        start_y = pdf.get_y()
        pdf.cell(40, 15, str(res.milestone), 1)
        pdf.cell(25, 15, f"FL {res.floor}", 1)
        pdf.cell(25, 15, f"{res.confidence*100:.0f}%", 1)
        
        # Use multi_cell for the notes column to allow wrapping
        curr_x = pdf.get_x()
        pdf.multi_cell(100, 5, res.evidence_notes, 1)
        pdf.set_xy(curr_x + 100, start_y + 15) 
        pdf.ln(0)
        
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG & THEME ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; }}
    h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']}; }}
    .stButton>button {{ background-color: {BRAND_THEME['SADDLE_BROWN']}; color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=60)
    st.title("SentinelScope AI")
    
    # Ensure Secrets exist
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP"])
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
        
        st.write("Syncing NYC DOB Data (BIS/DOB NOW)...")
        live_violations = fetch_live_dob_alerts({"bbl": bbl})
        
        st.write("Processing High-Res Imagery...")
        # Process once, save findings
        raw_findings = [batch_processor._process_single_image(f) for f in uploads]
        
        found_milestones = list(set([f.milestone for f in raw_findings if f.milestone != "Unknown"]))
        analysis = gap_engine.detect_gaps(found_milestones)
        
        # Save to session state to prevent refresh-loss
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
    tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress", "🚨 DOB Compliance", "🛡️ Insurance Export"])

    with tab1:
        st.header(f"Site Intelligence: {res['meta']['address']}")
        map_data = pd.DataFrame({'lat': [res['geo_info']['lat']], 'lon': [res['geo_info']['lon']]})
        st.map(map_data, zoom=15)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Compliance Score", f"{res['analysis'].compliance_score}%")
        c2.metric("Risk Level", "HIGH" if res['analysis'].risk_score > 30 else "LOW")
        c3.metric("BBL Identifier", res['geo_info'].get('bbl', 'N/A'))
        
        st.info(f"**Next Priority:** {res['analysis'].next_priority}")

    with tab2:
        st.header("NYC Department of Buildings Sync")
        if res['live_violations']:
            st.error(f"🚨 {len(res['live_violations'])} Active Violations Detected")
            st.dataframe(res['live_violations'], use_container_width=True)
        else:
            st.success("✅ No active violations found for this BBL.")

    with tab3:
        st.header("Forensic Evidence Export")
        st.write("Verified audit trail for Insurance TCO and Risk Management.")
        
        pdf_bytes = create_pdf_report(res['meta']['name'], res['meta']['address'], res['analysis'], res['raw_findings'])
        
        st.download_button(
            label="📄 Download Forensic PDF Report",
            data=pdf_bytes,
            file_name=f"SentinelReport_{res['geo_info'].get('bbl', 'Audit')}.pdf",
            mime="application/pdf"
        )
        
        # Display finding summary
        df_display = pd.DataFrame([f.dict() for f in res['raw_findings']])
        st.table(df_display[['milestone', 'floor', 'zone', 'confidence', 'evidence_notes']])
else:
    st.title("SentinelScope AI Command Center")
    st.info("👋 Welcome. Please use the sidebar to upload site images and initialize the forensic audit.")
