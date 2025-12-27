"""
SentinelScope | All-in-One AI Construction Dashboard
Integrated: Open360, Live NYC DOB API, Map View, and PDF Reporting.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
from fpdf import FPDF
from typing import Dict, List

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME
from core.geocoding import lookup_address
from core.dob_engine import fetch_live_dob_alerts
from core.gap_detector import detect_gaps

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

def create_pdf_report(p_name, address, analysis, df):
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
    pdf.cell(60, 10, "Date Captured", 1)
    pdf.cell(40, 10, "AI Confidence", 1)
    pdf.ln()
    
    # Table Content
    for _, row in df[df['confidence'] > 0.85].iterrows():
        pdf.cell(60, 10, str(row['milestone']), 1)
        pdf.cell(60, 10, str(datetime.now().strftime("%Y-%m-%d")), 1)
        pdf.cell(40, 10, f"{row['confidence']*100:.1f}%", 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# ====== UI CONFIG ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

# (Inject theme logic from previous versions here)

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
    
    # 2. Parallel Processing
    with st.spinner("🕵️ Syncing Visuals and NYC Data..."):
        live_violations = fetch_live_dob_alerts({"bbl": bbl})
        data_path = "data/mock_frames.csv"
        df = pd.read_csv(data_path)
        found_milestones = df['milestone'].unique().tolist()
        analysis = detect_gaps(found_milestones, p_type)

    tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress", "🚨 DOB Compliance", "🛡️ Insurance Export"])

    # TAB 1: VISUAL PROGRESS + MAP
    with tab1:
        st.header("Site Intelligence & Mapping")
        
        # New Map Feature
        map_data = pd.DataFrame({'lat': [geo_info['lat']], 'lon': [geo_info['lon']]})
        st.map(map_data, zoom=15)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image("https://images.unsplash.com/photo-1541888946425-d81bb19480c5?q=80&w=1200", use_container_width=True)
        with col2:
            st.metric("Site BBL", bbl)
            st.metric("Compliance", f"{analysis.compliance_score}%")

    # TAB 2: DOB ALERTS (Same logic as before)
    with tab2:
        st.header("NYC DOB Proactive Monitoring")
        if live_violations:
            st.error(f"🚨 {len(live_violations)} Violations Found")
            st.write(live_violations)
        else:
            st.success("✅ No current violations.")

    # TAB 3: INSURANCE + PDF GENERATOR
    with tab3:
        st.header("Insurance Evidence Export")
        st.info("The system has prepared a professional PDF summary of all high-confidence evidence.")
        
        # Professional PDF Generator
        pdf_bytes = create_pdf_report(p_name, address, analysis, df)
        
        st.download_button(
            label="📄 Download Professional PDF Report",
            data=pdf_bytes,
            file_name=f"SentinelReport_{p_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        # Raw Data View
        st.dataframe(df[df['confidence'] > 0.85], use_container_width=True)

else:
    st.title("SentinelScope AI Command Center")
    st.markdown("Enter project details to generate a compliance map and insurance-ready report.")
