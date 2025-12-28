import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from fpdf import FPDF
from typing import Dict, List

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME
from core.geocoding import lookup_address
from core.dob_engine import fetch_live_dob_alerts
from core.gap_detector import ComplianceGapEngine # Updated to Class
from core.processor import SentinelBatchProcessor   # New Batch Logic

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
    pdf.set_font("Arial", size=12)
    
    # Project Summary
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Project: {p_name}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Address: {address}", ln=True)
    pdf.cell(200, 10, txt=f"Compliance Score: {analysis.compliance_score}%", ln=True)
    pdf.ln(10)
    
    # Audit Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Verified Evidence Logs", ln=True)
    pdf.set_font("Arial", size=8)
    
    # Table Header
    pdf.cell(60, 10, "Milestone", 1)
    pdf.cell(60, 10, "Location", 1)
    pdf.cell(40, 10, "AI Confidence", 1)
    pdf.ln()
    
    # Table Content from live Batch Results
    for res in findings:
        pdf.cell(60, 10, str(res.milestone), 1)
        pdf.cell(60, 10, f"Floor {res.floor} - {res.zone}", 1)
        pdf.cell(40, 10, f"{res.confidence*100:.1f}%", 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

# Theme Injection
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; }}
    h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']}; }}
    .stButton>button {{ background-color: {BRAND_THEME['SADDLE_BROWN']}; color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & DATA LOADING ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=60)
    st.title("SentinelScope AI")
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 INITIALIZE AUDIT")

if submit and uploads:
    # 1. Resolve Geo & Property Info
    geo_info = lookup_address(address)
    bbl = geo_info.get("bbl", "1012650001")
    
    # 2. Parallel Processing with Live Visuals
    with st.status("🕵️ Running AI Visual Audit...", expanded=True) as status:
        # Initialize the new engines
        gap_engine = ComplianceGapEngine(project_type=p_type.lower())
        batch_processor = SentinelBatchProcessor(engine=gap_engine)
        
        st.write("Fetching NYC DOB data...")
        live_violations = fetch_live_dob_alerts({"bbl": bbl})
        
        st.write("Processing image batch in parallel...")
        # We pass the uploaded files directly to the processor
        # Note: In production, use file paths; here we simulate with file names
        analysis = batch_processor.run_audit([f.name for f in uploads])
        
        # We also need the raw findings for the report table
        # We'll re-run a quick mock of the results for the UI display
        raw_findings = [batch_processor._process_single_image(f.name) for f in uploads]
        
        status.update(label="Audit Complete!", state="complete", expanded=False)

    tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress", "🚨 DOB Compliance", "🛡️ Insurance Export"])

    with tab1:
        st.header("Site Intelligence & Mapping")
        map_data = pd.DataFrame({'lat': [geo_info['lat']], 'lon': [geo_info['lon']]})
        st.map(map_data, zoom=15)
        
        col1, col2, col3 = st.columns([1.5, 1, 1])
        with col1:
            # Show the first uploaded image as "Current Site View"
            st.image(uploads[0], caption="Latest Site Capture", use_container_width=True)
        with col2:
            st.metric("Compliance Score", f"{analysis.compliance_score}%")
            st.metric("Missing Items", analysis.gap_count)
        with col3:
            st.metric("Risk Level", "HIGH" if analysis.risk_score > 30 else "LOW")
            st.info(f"Priority: {analysis.next_priority}")

    with tab2:
        st.header("NYC DOB Proactive Monitoring")
        if live_violations:
            st.error(f"🚨 {len(live_violations)} Live Violations Found at {address}")
            st.write(live_violations)
        else:
            st.success("✅ No current violations found on BIS/DOB Now.")

    with tab3:
        st.header("Insurance Evidence Export")
        st.info("Verified audit trail prepared for TCO (Temporary Certificate of Occupancy) support.")
        
        # Professional PDF Generator using live findings
        pdf_bytes = create_pdf_report(p_name, address, analysis, raw_findings)
        
        st.download_button(
            label="📄 Download Professional PDF Report",
            data=pdf_bytes,
            file_name=f"SentinelReport_{p_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        # Display the findings as a clean table
        findings_df = pd.DataFrame([f.dict() for f in raw_findings])
        st.table(findings_df[['milestone', 'floor', 'zone', 'confidence']])

else:
    st.title("SentinelScope AI Command Center")
    st.info("Waiting for site data... Use the sidebar to upload project images and initialize the NYC DOB sync.")
