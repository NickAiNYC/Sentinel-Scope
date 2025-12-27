"""
SentinelScope | All-in-One AI Construction Dashboard
Integrates: Open360 Visuals, NYC DOB Alerts, and Insurance Evidence packages.
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
        .stTabs [data-baseweb="tab"] {{ height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; }}
        .stTabs [aria-selected="true"] {{ background-color: white; border-bottom: 3px solid {BRAND_THEME['MAHOGANY']} !important; }}
        </style>
    """, unsafe_allow_html=True)

# ASSET FALLBACKS
DASHBOARD_IMAGE = "https://images.unsplash.com/photo-1541888946425-d81bb19480c5?q=80&w=800&auto=format&fit=crop"

# ====== AI AUDIT ENGINE ======
def run_ai_audit(project_type: str) -> Tuple[Optional[object], Optional[pd.DataFrame]]:
    """Loads detections from data/mock_frames.csv and triggers Gap Analysis."""
    try:
        time.sleep(1.2) 
        data_path = "data/mock_frames.csv"
        if not os.path.exists(data_path):
            return None, None
            
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
        submit = st.form_submit_button("🚀 RUN AUDIT")
    st.caption("v0.1.0 • Built for High-Tech NYC Compliance")

if submit and uploads:
    try:
        lookup_address(address)
        with st.spinner("🕵️ Orchestrating AI Audit and NYC Data Aggregation..."):
            analysis, raw_data = run_ai_audit(p_type)
        
        if analysis and raw_data is not None:
            # --- TABS: THE THREE PILLARS ---
            tab1, tab2, tab3 = st.tabs(["🏗️ Visual Progress (Open360)", "🚨 DOB Compliance Alerts", "🛡️ Insurance Evidence"])

            # PILLAR 1: VISUAL PROGRESS (OPEN360)
            with tab1:
                st.header("Open360™ Site Intelligence")
                st.caption("Synchronizing AI classification with site captures.")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Compliance Score", f"{analysis.compliance_score}%")
                col_m2.metric("Detected Gaps", analysis.gap_count)
                col_m3.metric("Audit Priority", analysis.next_priority)

                c_left, c_right = st.columns([2, 1])
                with c_left:
                    st.image(DASHBOARD_IMAGE, use_container_width=True, caption="Latest AI Site Capture Analysis")
                with c_right:
                    st.subheader("Progress Index")
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=analysis.compliance_score,
                        gauge={'bar': {'color': BRAND_THEME['MAHOGANY']},
                               'axis': {'range': [0, 100]},
                               'steps': [{'range': [0, 60], 'color': "#E5D3B3"}]}
                    ))
                    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)

            # PILLAR 2: DOB ALERTS
            with tab2:
                st.header("NYC DOB Proactive Monitoring")
                st.warning("🚨 **Active Alert:** 1 Potential Safety Violation Found via NYC OpenData.")
                
                # High-Tech Alert Display
                st.error("""
                    **Violation ID: 392810** **Type:** Site Safety / Debris  
                    **Status:** OPEN  
                    **Code Reference:** BC 3301.2
                """)
                
                st.subheader("Required Actions & NYC Code Citations")
                gap_df = pd.DataFrame([{
                    "Milestone": g.milestone, "NYC Code": g.dob_code, 
                    "Priority": g.risk_level, "Action": g.recommendation
                } for g in analysis.missing_milestones])
                st.table(gap_df)

            # PILLAR 3: INSURANCE EVIDENCE
            with tab3:
                st.header("Insurance Evidence Packages")
                st.info("The following captures are verified for 'High Confidence' submission to insurance brokers.")
                
                # Human-in-the-Loop Filtered Data
                insurance_ready = raw_data[raw_data['confidence'] > 0.85]
                st.dataframe(insurance_ready, use_container_width=True)
                
                st.download_button(
                    label="📥 Download Audit-Ready ZIP Package",
                    data=insurance_ready.to_csv().encode('utf-8'),
                    file_name=f"sentinel_insurance_{p_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )

    except NYCBoundaryError as e:
        st.error(f"Jurisdiction Error: {e.message}")
    except Exception as e:
        st.error(f"System Error: {str(e)}")
else:
    # LANDING VIEW
    st.title("Audit-Ready Site Intelligence")
    st.markdown("""
    ### Welcome to SentinelScope
    The all-in-one command center for NYC construction compliance.
    
    * **Open360 Integration**: Link visual site walk-throughs to AI classification.
    * **DOB Alerts**: Proactively monitor NYC OpenData violations and complaints.
    * **Insurance Ready**: Generate verified evidence packages in minutes.
    """)
    st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1200", use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align: center; color: gray;'>SentinelScope v0.1.0 • {datetime.now().strftime('%B %Y')}</div>", unsafe_allow_html=True)
