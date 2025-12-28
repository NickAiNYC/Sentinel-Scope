import streamlit as st
import pandas as pd
import sys
import os
import json
from datetime import datetime
from fpdf import FPDF
from typing import List, Union

# ====== STREAMLIT CLOUD PATH FIX ======
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ====== CORE MODULE IMPORTS ======
try:
    from core.geocoding import lookup_address
    from core.dob_engine import DOBEngine  
    from core.gap_detector import ComplianceGapEngine
    from core.processor import SentinelBatchProcessor
except ImportError as e:
    st.error(f"Critical Import Error: {e}. Check your folder structure.")
    st.stop()

# ====== PDF GENERATION ENGINE ======
class SentinelReport(FPDF):
    def header(self):
        self.set_fill_color(33, 47, 61)
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 15, 'SENTINEL-SCOPE AI | CONSTRUCTION FORENSICS', 0, 1, 'L')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, 'NYC BC 2022/2025 Compliance Verification & Risk Evidence', 0, 1, 'L')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f'Forensic Log | Generated: {timestamp} | Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(p_name, address, analysis, findings: List):
    pdf = SentinelReport()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_text_color(93, 64, 55)
    pdf.cell(0, 10, txt=f"PROJECT: {p_name.upper()}", ln=True)
    pdf.set_font("helvetica", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, txt=f"LOCATION: {address}", ln=True)
    pdf.cell(0, 7, txt=f"COMPLIANCE RATING: {analysis.compliance_score}%", ln=True)
    pdf.ln(10)
    
    # Table headers
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(45, 10, "Milestone", 1, 0, 'C', True)
    pdf.cell(20, 10, "Floor", 1, 0, 'C', True)
    pdf.cell(20, 10, "Conf.", 1, 0, 'C', True)
    pdf.cell(105, 10, "Evidence Narrative", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", size=9)
    for res in findings:
        m_name = getattr(res, 'milestone', 'N/A')
        f_level = getattr(res, 'floor', 'N/A')
        conf_val = getattr(res, 'confidence', 0)
        evidence = getattr(res, 'evidence_notes', 'No narrative.')
        
        start_y = pdf.get_y()
        pdf.set_x(95)
        pdf.multi_cell(105, 6, evidence, border=1)
        end_y = pdf.get_y()
        row_height = max(10, end_y - start_y)
        
        pdf.set_xy(10, start_y)
        pdf.cell(45, row_height, str(m_name), 1)
        pdf.cell(20, row_height, f"FL {f_level}", 1)
        pdf.cell(20, row_height, f"{conf_val*100:.0f}%", 1)
        pdf.set_y(end_y)
        
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

# Persistent State Management
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=70)
    st.title("SentinelScope AI")
    st.caption("Forensic Site Analysis Engine v2.6")
    st.markdown("---")
    
    api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Audit Focus", ["Structural", "MEP", "Fireproofing", "Foundation"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        submit = st.form_submit_button("🚀 INITIALIZE AUDIT", use_container_width=True)

# --- AUDIT EXECUTION ---
if submit and uploads:
    if not api_key:
        st.error("Missing DEEPSEEK_API_KEY in Streamlit Secrets.")
    else:
        with st.status("🕵️ Running AI Visual Audit...", expanded=True) as status:
            st.write("🛰️ Geocoding location & pulling NYC DOB Records...")
            geo_info = lookup_address(address)
            bbl = geo_info.get("bbl", "1012650001")
            live_violations = DOBEngine.fetch_live_dob_alerts({"bbl": bbl})
            
            gap_engine = ComplianceGapEngine(project_type=p_type.lower())
            batch_processor = SentinelBatchProcessor(engine=gap_engine, api_key=api_key)
            
            st.write("👁️ Analyzing visual evidence...")
            raw_findings = batch_processor.run_audit(uploads)
            
            st.write("📊 Calculating NYC BC 2022 Compliance Gaps...")
            analysis = batch_processor.finalize_gap_analysis(raw_findings)
            
            st.session_state.audit_results = {
                "analysis": analysis,
                "raw_findings": raw_findings,
                "geo_info": geo_info,
                "live_violations": live_violations,
                "meta": {"name": p_name, "address": address, "uploads": uploads}
            }
            status.update(label="Audit Complete!", state="complete", expanded=False)
            st.rerun()

# --- DASHBOARD DISPLAY ---
if st.session_state.audit_results:
    res = st.session_state.audit_results
    analysis = res['analysis']
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliance Score", f"{analysis.compliance_score}%")
    c2.metric("Forensic Risk", f"{analysis.risk_score}/100")
    c3.metric("Validated Milestones", len(res['raw_findings']))
    c4.metric("BBL ID", res['geo_info'].get('bbl', 'N/A'))

    tab1, tab2, tab3 = st.tabs(["🏗️ SPATIAL AUDIT", "🚨 DOB VIOLATIONS", "🛡️ EXPORT LOGS"])

    with tab1:
        st.subheader("Field Progress & Visual Evidence")
        col_map, col_img = st.columns([1.5, 1])
        with col_map:
            map_df = pd.DataFrame({'lat': [res['geo_info']['lat']], 'lon': [res['geo_info']['lon']]})
            st.map(map_df, zoom=16)
        with col_img:
            st.image(res['meta']['uploads'][0], caption="Latest Field Capture", use_container_width=True)
            st.warning(f"**NEXT PRIORITY:** {analysis.next_priority}")

    with tab2:
        st.subheader("Active DOB Department Sync")
        if res['live_violations']:
            st.error(f"🚨 {len(res['live_violations'])} ACTIVE VIOLATIONS ON BBL {res['geo_info'].get('bbl')}")
            st.dataframe(res['live_violations'], use_container_width=True)
        else:
            st.success("✅ No open safety violations found.")

    with tab3:
        st.subheader("Generate Forensic PDF Report")
        pdf_data = create_pdf_report(res['meta']['name'], res['meta']['address'], analysis, res['raw_findings'])
        st.download_button("📄 DOWNLOAD FORENSIC LOG", data=pdf_data, file_name="SentinelReport.pdf", mime="application/pdf")
        
        st.button("Clear Audit", on_click=lambda: st.session_state.update(audit_results=None))
else:
    st.title("Welcome to SentinelScope AI")
    st.info("👈 Use the sidebar to upload site captures and begin the forensic audit.")
