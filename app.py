import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from typing import List

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME
from core.geocoding import lookup_address
from core.dob_engine import fetch_live_dob_alerts
from core.gap_detector import ComplianceGapEngine
from core.processor import SentinelBatchProcessor

# ====== PDF GENERATION ENGINE ======
class SentinelReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'SentinelScope AI | Construction Evidence Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d")}', 0, 0, 'C')

def create_pdf_report(p_name, address, analysis, findings: List):
    pdf = SentinelReport()
    pdf.add_page()
    
    # Project Summary Header
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(139, 69, 19) # PRIMARY_BROWN
    pdf.cell(200, 10, txt=f"Project: {p_name}", ln=True)
    
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 7, txt=f"Address: {address}", ln=True)
    pdf.cell(200, 7, txt=f"Compliance Score: {analysis.compliance_score}%", ln=True)
    pdf.ln(10)
    
    # Audit Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Verified Evidence Logs", ln=True)
    
    # Table Header
    pdf.set_fill_color(245, 245, 220) # BACKGROUND_BEIGE
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(40, 10, "Milestone", 1, 0, 'C', True)
    pdf.cell(30, 10, "Location", 1, 0, 'C', True)
    pdf.cell(25, 10, "Confidence", 1, 0, 'C', True)
    pdf.cell(95, 10, "Forensic Evidence Notes", 1, 1, 'C', True)
    
    # Table Content
    pdf.set_font("Arial", size=8)
    for res in findings:
        # We use multi_cell for notes to allow text wrapping
        start_y = pdf.get_y()
        pdf.cell(40, 15, str(res.milestone), 1)
        pdf.cell(30, 15, f"Floor {res.floor}", 1)
        pdf.cell(25, 15, f"{res.confidence*100:.1f}%", 1)
        
        # Reset X to the notes column and use multi_cell
        curr_x = pdf.get_x()
        pdf.multi_cell(95, 5, res.evidence_notes, 1)
        pdf.set_xy(curr_x + 95, start_y + 15) # Move to next row
        pdf.ln(0)
        
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG & SESSION STATE ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

# Persistent storage for audit results
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=60)
    st.title("SentinelScope AI")
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 INITIALIZE AUDIT")

# --- AUDIT LOGIC ---
if submit and uploads:
    geo_info = lookup_address(address)
    bbl = geo_info.get("bbl", "1012650001")
    
    with st.status("🕵️ Running AI Visual Audit...", expanded=True) as status:
        gap_engine = ComplianceGapEngine(project_type=p_type.lower())
        # Use st.secrets for the API key in production!
        batch_processor = SentinelBatchProcessor(engine=gap_engine, api_key=st.secrets["DEEPSEEK_API_KEY"])
        
        st.write("Fetching NYC DOB data...")
        live_violations = fetch_live_dob_alerts({"bbl": bbl})
        
        st.write("Analyzing imagery...")
        # CRITICAL: We process once and store the result objects
        raw_findings = [batch_processor._process_single_image(f) for f in uploads]
        
        # Run gap analysis on the detected milestones
        found_milestones = list(set([f.milestone for f in raw_findings if f.milestone != "Unknown"]))
        analysis = gap_engine.detect_gaps(found_milestones)
        
        # Save to session state
        st.session_state.audit_results = {
            "analysis": analysis,
            "raw_findings": raw_findings,
            "geo_info": geo_info,
            "live_violations": live_violations
        }
        status.update(label="Audit Complete!", state="complete", expanded=False)

# --- DASHBOARD DISPLAY ---
if st.session_state.audit_results:
    res = st.session_state.audit_results
    tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress", "🚨 DOB Compliance", "🛡️ Insurance Export"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.header("Site Intelligence")
            st.map(pd.DataFrame({'lat': [res['geo_info']['lat']], 'lon': [res['geo_info']['lon']]}), zoom=15)
        with col2:
            st.metric("Compliance Score", f"{res['analysis'].compliance_score}%")
            st.metric("Missing Items", res['analysis'].gap_count)
            st.info(f"Priority: {res['analysis'].next_priority}")

    with tab2:
        if res['live_violations']:
            st.error(f"🚨 {len(res['live_violations'])} Live Violations Found")
            st.write(res['live_violations'])
        else:
            st.success("✅ No current violations found on BIS/DOB Now.")

    with tab3:
        st.header("Insurance Evidence Export")
        pdf_bytes = create_pdf_report(p_name, address, res['analysis'], res['raw_findings'])
        
        st.download_button(
            label="📄 Download Professional PDF Report",
            data=pdf_bytes,
            file_name=f"SentinelReport_{p_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.table(pd.DataFrame([f.dict() for f in res['raw_findings']]))
else:
    st.info("Upload project images in the sidebar to begin.")
