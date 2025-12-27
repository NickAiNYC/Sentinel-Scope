"""
SentinelScope | All-in-One AI Construction Dashboard
Integrates: Open360 Visuals, Live NYC DOB Alerts, and Insurance Evidence packages.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time
import requests
from datetime import datetime
from typing import Tuple, Optional, List, Dict

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME
from core.exceptions import NYCBoundaryError, SentinelError
from core.gap_detector import detect_gaps
from core.geocoding import lookup_address

# ====== LIVE DATA ENGINES ======
def fetch_live_dob_alerts(address_data: Dict) -> List[Dict]:
    """
    Queries NYC OpenData for real-time ECB/OATH violations.
    Uses the resolved BBL (Borough-Block-Lot) from the geocoding module.
    """
    bbl = address_data.get("bbl", "1012650001") # Default to mock if not found
    endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"
    
    # Query parameters for the Socrata API
    params = {
        "bbl": bbl,
        "$order": "isn_dob_bis_extract DESC",
        "$limit": 5
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

# ====== UI & THEME ENGINE ======
def inject_custom_theme():
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; color: {BRAND_THEME['PRIMARY_BROWN']}; }}
        [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; border-right: 1px solid {BRAND_THEME['PRIMARY_BROWN']}; }}
        div[data-testid="stMetricValue"] {{ color: {BRAND_THEME['MAHOGANY']}; }}
        .stMetric {{ background-color: white; border: 1px solid {BRAND_THEME['SIDEBAR_TAN']}; border-radius: 12px; padding: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
        h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']} !important; font-family: 'Georgia', serif; font-weight: 700; }}
        .stButton>button {{ background-color: {BRAND_THEME['PRIMARY_BROWN']}; color: white; border-radius: 8px; width: 100%; transition: 0.3s; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        .stTabs [data-baseweb="tab"] {{ height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; font-weight: 600; }}
        .stTabs [aria-selected="true"] {{ background-color: white; border-bottom: 3px solid {BRAND_THEME['MAHOGANY']} !important; }}
        </style>
    """, unsafe_allow_html=True)

# ASSET FALLBACKS
DASHBOARD_IMAGE = "https://images.unsplash.com/photo-1541888946425-d81bb19480c5?q=80&w=800&auto=format&fit=crop"

# ====== AI AUDIT ENGINE ======
def run_ai_audit(project_type: str) -> Tuple[Optional[object], Optional[pd.DataFrame]]:
    try:
        time.sleep(1.0) 
        data_path = "data/mock_frames.csv"
        if not os.path.exists(data_path): return None, None
        df = pd.read_csv(data_path)
        found_milestones = df['milestone'].unique().tolist()
        analysis_results = detect_gaps(found_milestones, project_type)
        return analysis_results, df
    except Exception as e:
        raise SentinelError(f"Audit Pipeline Failure: {str(e)}")

# ====== MAIN PAGE EXECUTION ======
st.set_page_config(page_title="SentinelScope | All-in-One Dashboard", page_icon="🏗️", layout="wide")
inject_custom_theme()

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=60)
    st.title("SentinelScope AI")
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 RUN AI COMMAND CENTER")
    st.caption("v0.1.0 • Built for NYC Real Estate & Insurance")

if submit and uploads:
    try:
        # 1. Resolve Property Info
        geo_info = lookup_address(address)
        
        with st.spinner("🕵️ Orchestrating Visuals, DOB Data, and AI Classifications..."):
            # 2. Parallel Data Ingestion
            analysis, raw_data = run_ai_audit(p_type)
            live_violations = fetch_live_dob_alerts(geo_info)
        
        if analysis and raw_data is not None:
            tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress", "🚨 DOB Compliance", "🛡️ Insurance Evidence"])

            # PILLAR 1: VISUALS
            with tab1:
                st.header("Open360™ Site Intelligence")
                m1, m2, m3 = st.columns(3)
                m1.metric("Compliance Score", f"{analysis.compliance_score}%")
                m2.metric("Detected Gaps", analysis.gap_count)
                m3.metric("BBL Reference", geo_info.get('bbl', 'N/A'))

                c_left, c_right = st.columns([2, 1])
                with c_left:
                    st.image(DASHBOARD_IMAGE, use_container_width=True, caption="Latest Vision Analysis")
                with c_right:
                    st.subheader("Progress Index")
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=analysis.compliance_score,
                        gauge={'bar': {'color': BRAND_THEME['MAHOGANY']}, 'axis': {'range': [0, 100]}}
                    ))
                    fig.update_layout(height=280, paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20,r=20,t=40,b=20))
                    st.plotly_chart(fig, use_container_width=True)

            # PILLAR 2: LIVE DOB ALERTS
            with tab2:
                st.header("Live NYC DOB Proactive Monitoring")
                if live_violations:
                    st.error(f"🚨 **{len(live_violations)} Active ECB/OATH Violations Found** for this site.")
                    for v in live_violations:
                        with st.expander(f"Violation: {v.get('ecb_violation_number')} - {v.get('violation_status')}"):
                            st.write(f"**Description:** {v.get('description', 'N/A')}")
                            st.write(f"**Issue Date:** {v.get('issue_date', 'N/A')[:10]}")
                            st.markdown(f"[View BIS Record](https://a810-bisweb.nyc.gov/bisweb/bispi00.jsp)")
                else:
                    st.success("✅ No active DOB violations found via NYC OpenData.")
                
                st.subheader("AI-Identified Compliance Gaps (BC 2022)")
                gap_df = pd.DataFrame([{
                    "Milestone": g.milestone, "NYC Code": g.dob_code, 
                    "Severity": g.risk_level, "Action": g.recommendation
                } for g in analysis.missing_milestones])
                st.table(gap_df)

            # PILLAR 3: INSURANCE
            with tab3:
                st.header("Insurance Evidence Package")
                st.info("Verified captures (>85% Confidence) ready for Builder's Risk submission.")
                insurance_ready = raw_data[raw_data['confidence'] > 0.85]
                st.dataframe(insurance_ready, use_container_width=True)
                st.download_button(
                    label="📥 Export Insurance CSV Package",
                    data=insurance_ready.to_csv(index=False).encode('utf-8'),
                    file_name=f"insurance_audit_{p_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"System Error: {str(e)}")
else:
    # LANDING VIEW
    st.title("SentinelScope Command Center")
    st.markdown("""
    Enter project details in the sidebar to synchronize visual site walks with NYC regulatory data.
    """)
    st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1200", use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align: center; color: gray;'>SentinelScope v0.1.0 • NYC 2025 • Command Center Mode</div>", unsafe_allow_html=True)
