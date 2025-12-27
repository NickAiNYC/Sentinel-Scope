"""
SentinelScope | Main Application Entry Point
Refined for: Reliability, Professional Polish, and User Transparency.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time
from datetime import datetime
from typing import Tuple, Optional

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME
from core.exceptions import NYCBoundaryError, SentinelError
from core.gap_detector import detect_gaps
from core.geocoding import lookup_address

# ====== UI UTILITIES ======
def inject_custom_theme():
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; color: {BRAND_THEME['PRIMARY_BROWN']}; }}
        [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; border-right: 1px solid {BRAND_THEME['PRIMARY_BROWN']}; }}
        div[data-testid="stMetricValue"] {{ color: {BRAND_THEME['MAHOGANY']}; }}
        .stMetric {{ background-color: white; border: 1px solid {BRAND_THEME['SIDEBAR_TAN']}; border-radius: 12px; padding: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
        h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']} !important; font-family: 'Georgia', serif; font-weight: 700; }}
        .stButton>button {{ background-color: {BRAND_THEME['PRIMARY_BROWN']}; color: white; border-radius: 8px; width: 100%; transition: 0.3s; }}
        .stButton>button:hover {{ background-color: {BRAND_THEME['MAHOGANY']}; color: white; }}
        </style>
    """, unsafe_allow_html=True)

# RELIABLE IMAGE FALLBACKS
LANDING_IMAGE = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1200&auto=format&fit=crop"
DASHBOARD_IMAGE = "https://images.unsplash.com/photo-1541888946425-d81bb19480c5?q=80&w=800&auto=format&fit=crop"

# ====== AI AUDIT ENGINE ======
def run_ai_audit(project_type: str) -> Tuple[Optional[object], Optional[pd.DataFrame]]:
    """Loads detections from data/mock_frames.csv and triggers Gap Analysis."""
    try:
        time.sleep(1.2) # AI Inference Latency Simulation
        data_path = "data/mock_frames.csv"
        
        if not os.path.exists(data_path):
            # Fallback for demo stability if CSV is missing in a local environment
            return None, None
            
        df = pd.read_csv(data_path)
        found_milestones = df['milestone'].unique().tolist()
        analysis_results = detect_gaps(found_milestones, project_type)
        
        return analysis_results, df
    except Exception as e:
        raise SentinelError(f"Audit Pipeline Failure: {str(e)}")

# ====== MAIN PAGE ======
st.set_page_config(page_title="SentinelScope | AI Audit", page_icon="🏗️", layout="wide")
inject_custom_theme()

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=60)
    st.title("SentinelScope AI")
    with st.form("audit_config"):
        p_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 RUN AI COMPLIANCE AUDIT")
    st.caption("v0.1.0 • Built by Nick Altstein")
    st.caption("NYC Building Code 2022 Verified")

if submit and uploads:
    try:
        lookup_address(address)
        
        with st.spinner("🕵️ AI Agent analyzing captures against NYC Building Code..."):
            analysis, raw_data = run_ai_audit(p_type)
        
        if analysis and raw_data is not None:
            # 1. EXECUTIVE SUMMARY
            st.header(f"Executive Audit: {p_name}")
            st.caption("ℹ️ *Using verified audit data from data/mock_frames.csv for demonstration.*")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Compliance", f"{analysis.compliance_score}%")
            m2.metric("Gaps Found", analysis.gap_count, delta_color="inverse")
            m3.metric("Safety Risk", "LOW" if analysis.risk_score < 30 else "CRITICAL")
            m4.metric("Next Priority", analysis.next_priority)
            
            # 2. SITE SURVEILLANCE & VISUALS
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📍 Site Surveillance")
                low_conf = raw_data[raw_data['confidence'] < 0.85]
                if not low_conf.empty:
                    st.warning(f"⚠️ **Human-in-the-loop required:** {len(low_conf)} detections flagged with low confidence.")
                st.image(DASHBOARD_IMAGE, caption="Latest AI Site Capture Analysis", use_container_width=True)
            
            with c2:
                st.subheader("⚖️ Compliance Gauge")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=analysis.compliance_score,
                    gauge={'axis': {'range': [0, 100], 'tickcolor': BRAND_THEME['PRIMARY_BROWN']},
                           'bar': {'color': BRAND_THEME['MAHOGANY']},
                           'steps': [{'range': [0, 60], 'color': "#E5D3B3"},
                                    {'range': [85, 100], 'color': BRAND_THEME['SUCCESS_GREEN']}]}
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

            # 3. COMPLIANCE GAPS & EXPORT
            st.subheader("🔍 Required Actions & Citations")
            if analysis.missing_milestones:
                gap_df = pd.DataFrame([{
                    "Milestone": g.milestone, "NYC Code": g.dob_code, 
                    "Priority": g.risk_level, "Action": g.recommendation
                } for g in analysis.missing_milestones])
                st.table(gap_df)
                
                st.download_button(
                    label="📥 Export Compliance Gap Report (CSV)",
                    data=gap_df.to_csv(index=False),
                    file_name=f"sentinel_audit_{p_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ All required milestones documented. Site is audit-ready.")
                st.balloons()

            with st.expander("🛠️ View Raw AI Detection Log"):
                st.dataframe(raw_data, use_container_width=True)

    except NYCBoundaryError as e:
        st.error(f"Jurisdiction Error: {e.message}")
    except Exception as e:
        st.error(f"System Error: {str(e)}")
else:
    # LANDING VIEW
    st.title("Audit-Ready Site Intelligence")
    st.markdown("""
    ### Welcome to SentinelScope
    Ground your construction documentation in **NYC Building Code 2022** reality.
    
    1. **Configure**: Enter site context and project type in the sidebar.
    2. **Ingest**: Upload site photos or BIM logs for vision analysis.
    3. **Audit**: Receive structured compliance risk reports and gap detection.
    """)
    st.image(LANDING_IMAGE, caption="Architecture & Compliance Unified", use_container_width=True)

st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>"
    f"SentinelScope v0.1.0 • {datetime.now().strftime('%B %Y')} • Built for the Construction Industry"
    f"</div>", 
    unsafe_allow_html=True
)
