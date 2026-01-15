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
    from violations.dob.dob_engine import DOBEngine  
    from core.gap_detector import ComplianceGapEngine
    from core.processor import SentinelBatchProcessor
except ImportError as e:
    st.error(f"Critical Import Error: {e}")
    st.stop()

# ====== PDF GENERATION ENGINE ======
class SentinelReport(FPDF):
    def header(self):
        self.set_fill_color(33, 47, 61)
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
        self.cell(0, 10, f'Forensic Log | Generated: {timestamp} | Page {self.page_no()}', 0, 0, 'C')

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
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Milestone", 1, 0, 'C', True)
    pdf.cell(20, 10, "Floor", 1, 0, 'C', True)
    pdf.cell(20, 10, "Conf.", 1, 0, 'C', True)
    pdf.cell(110, 10, "Forensic Evidence Narrative", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=8)
    for res in findings:
        # Use getattr to safely handle Pydantic objects or dicts
        milestone = getattr(res, 'milestone', 'N/A')
        floor = getattr(res, 'floor', 'N/A')
        conf = getattr(res, 'confidence', 0)
        notes = getattr(res, 'evidence_notes', '')

        # Using multi_cell for the notes column to allow wrapping
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        pdf.cell(40, 15, str(milestone), 1)
        pdf.cell(20, 15, f"FL {floor}", 1)
        pdf.cell(20, 15, f"{conf*100:.0f}%", 1)
        pdf.multi_cell(110, 5, notes, 1)
        
    return bytes(pdf.output())

# ====== UI CONFIG & THEME ======
st.set_page_config(page_title="SentinelScope | AI Command Center", page_icon="🏗️", layout="wide")

# Theme styling
bg_color = BRAND_THEME.get('BACKGROUND_BEIGE', '#F5F5DC')
primary_color = BRAND_THEME.get('PRIMARY_BROWN', '#5D4037')

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    h1, h2, h3 {{ color: {primary_color}; font-weight: 800; }}
    </style>
    """, unsafe_allow_html=True)

if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=70)
    st.title("SentinelScope AI")
    st.markdown("---")
    
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
    else:
        geo_info = lookup_address(address)
        bbl = geo_info.get("bbl", "1012650001")
        
        with st.status("🕵️ Running AI Visual Audit...", expanded=True) as status:
            gap_engine = ComplianceGapEngine(project_type=p_type.lower())
            batch_processor = SentinelBatchProcessor(engine=gap_engine, api_key=api_key)
            
            st.write("🛰️ Pulling NYC DOB Records...")
            live_violations = DOBEngine.fetch_live_dob_alerts({"bbl": bbl})
            
            st.write("👁️ Analyzing Visual Compliance...")
            raw_findings = batch_processor.run_audit(uploads)
            
            st.write("📊 Calculating NYC BC 2022 Gaps...")
            analysis = batch_processor.finalize_gap_analysis(raw_findings)
            
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
    analysis = res['analysis']
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliance Score", f"{analysis.compliance_score}%")
    c2.metric("Risk Score", f"{analysis.risk_score}/100")
    c3.metric("Detected Milestones", len(res['raw_findings']))
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
            st.warning(f"**Action Required:** {analysis.next_priority}")

    with tab2:
        st.header("DOB Active Violation Sync")
        if res['live_violations']:
            st.error(f"🚨 FOUND {len(res['live_violations'])} ACTIVE VIOLATIONS")
            st.dataframe(res['live_violations'], use_container_width=True)
        else:
            st.success("✅ No active violations found for this Property Block (BBL).")

    with tab3:
        st.header("Forensic PDF Export")
        pdf_bytes = create_pdf_report(res['meta']['name'], res['meta']['address'], analysis, res['raw_findings'])
        
        st.download_button(
            label="📄 DOWNLOAD FORENSIC EVIDENCE LOG",
            data=pdf_bytes,
            file_name=f"SentinelReport_{res['meta']['name'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
        st.subheader("Compliance Remediation Plan")
        for gap in analysis.missing_milestones:
            with st.expander(f"❌ Missing: {gap.milestone}"):
                st.write(f"**Risk Level:** {gap.risk_level}")
                st.write(f"**AI Recommendation:** {gap.recommendation}")

else:
    st.info("Ready for Audit. Please upload site imagery via the sidebar to begin.")
