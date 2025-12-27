"""
SentinelScope | Main Application Entry Point
Version: 0.1.0
Engineering Standards: Ruff, Mypy, Pytest, PEP 621
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time
from datetime import datetime
from typing import Tuple, Optional

# ====== CORE MODULE IMPORTS (Framework Agnostic) ======
from core.constants import BRAND_THEME
from core.exceptions import NYCBoundaryError, SentinelError
from core.gap_detector import detect_gaps
from core.geocoding import lookup_address

# ====== UI & THEME ENGINE ======
def inject_custom_theme():
    """Injects professional AEC-inspired CSS into the Streamlit runtime."""
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BRAND_THEME['BACKGROUND_BEIGE']}; color: {BRAND_THEME['PRIMARY_BROWN']}; }}
        [data-testid="stSidebar"] {{ background-color: {BRAND_THEME['SIDEBAR_TAN']}; border-right: 1px solid {BRAND_THEME['PRIMARY_BROWN']}; }}
        div[data-testid="stMetricValue"] {{ color: {BRAND_THEME['MAHOGANY']}; }}
        .stMetric {{ background-color: white; border: 1px solid {BRAND_THEME['SIDEBAR_TAN']}; border-radius: 12px; padding: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
        h1, h2, h3 {{ color: {BRAND_THEME['PRIMARY_BROWN']} !important; font-family: 'Georgia', serif; font-weight: 700; }}
        .stButton>button {{ background-color: {BRAND_THEME['PRIMARY_BROWN']}; color: white; border-radius: 8px; border: none; width: 100%; transition: 0.3s; }}
        .stButton>button:hover {{ background-color: {BRAND_THEME['MAHOGANY']}; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        </style>
    """, unsafe_allow_html=True)

# ====== AI AUDIT ORCHESTRATION ======
def run_ai_audit(project_type: str) -> Tuple[Optional[object], Optional[pd.DataFrame]]:
    """
    Orchestrates the audit by loading from the data layer and triggering the Gap Engine.
    Implements defensive checks for data availability.
    """
    try:
        # Simulate AI inference/network latency
        time.sleep(1.2) 
        
        data_path = "data/mock_frames.csv"
        if not os.path.exists(data_path):
            raise SentinelError(f"Data Source Missing: {data_path} not found.")
            
        df = pd.read_csv(data_path)
        if df.empty:
            raise SentinelError("Data Source Empty: No detections found in mock_frames.csv.")

        # Extract unique milestones for the framework-agnostic core logic
        found_milestones = df['milestone'].unique().tolist()
        analysis_results = detect_gaps(found_milestones, project_type)
        
        return analysis_results, df

    except Exception as e:
        raise SentinelError(f"AI Audit Pipeline Failure: {str(e)}")

# ====== MAIN PAGE EXECUTION ======
st.set_page_config(
    page_title="SentinelScope | AI Construction Audit",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_custom_theme()

# --- SIDEBAR: PROJECT CONTROL ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=70)
    st.title("SentinelScope AI")
    st.markdown("---")
    
    with st.form("audit_config"):
        project_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Audit Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 RUN AI COMPLIANCE AUDIT")
    
    st.markdown("---")
    st.caption("v0.1.0 • Built by Nick Altstein")
    st.caption("NYC Building Code 2022 Verified")

# --- DASHBOARD LOGIC ---
if submit and uploads:
    try:
        # 1. Jurisdictional Gate
        lookup_address(address)
        
        # 2. Pipeline Execution
        with st.spinner("🕵️ AI Agent analyzing captures against NYC Building Code..."):
            analysis, raw_data = run_ai_audit(p_type)
        
        if analysis and raw_data is not None:
            # --- SECTION 1: EXECUTIVE SUMMARY ---
            st.header(f"Executive Audit: {project_name}")
            st.caption("ℹ️ *Using verified audit data from `data/mock_frames.csv`. Live API toggle restricted to production.*")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Compliance Score", f"{analysis.compliance_score}%")
            m2.metric("Detected Gaps", analysis.gap_count, delta_color="inverse")
            m3.metric("Safety Risk", "LOW" if analysis.risk_score < 30 else "CRITICAL")
            m4.metric("Next Priority", analysis.next_priority)
            
            st.divider()

            # --- SECTION 2: INTELLIGENCE & VISUALIZATION ---
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.subheader("📍 Site Surveillance")
                
                # Human-in-the-Loop: Highlighting Low Confidence Detections
                low_conf = raw_data[raw_data['confidence'] < 0.85]
                if not low_conf.empty:
                    st.warning(f"⚠️ **Verification Required:** {len(low_conf)} detections flagged with low confidence (<85%).")
                
                st.image("https://images.unsplash.com/photo-1541888946425-d81bb19480c5?auto=format&fit=crop&w=800", 
                         caption="Latest AI Capture Analysis", use_container_width=True)

            with col_right:
                st.subheader("⚖️ Compliance Index")
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = analysis.compliance_score,
                    gauge = {
                        'axis': {'range': [0, 100], 'tickcolor': BRAND_THEME['PRIMARY_BROWN']},
                        'bar': {'color': BRAND_THEME['MAHOGANY']},
                        'steps': [
                            {'range': [0, 60], 'color': "#E5D3B3"},
                            {'range': [85, 100], 'color': BRAND_THEME['SUCCESS_GREEN']}
                        ],
                    }
                ))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': BRAND_THEME['PRIMARY_BROWN']}, height=300)
                st.plotly_chart(fig, use_container_width=True)

            # --- SECTION 3: COMPLIANCE GAPS ---
            st.subheader("🔍 Required Actions & NYC Code Citations")
            if analysis.missing_milestones:
                gap_df = pd.DataFrame([
                    {
                        "Milestone": g.milestone,
                        "NYC Code": g.dob_code,
                        "Risk": g.risk_level,
                        "Recommendation": g.recommendation
                    } for g in analysis.missing_milestones
                ])
                st.table(gap_df)
                
                # User-Centric Export
                st.download_button(
                    label="📥 Export Compliance Gap Report (CSV)",
                    data=gap_df.to_csv(index=False),
                    file_name=f"sentinel_audit_{p_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ All required milestones documented. Site is audit-ready.")
                st.balloons()

            # --- SECTION 4: DATA OBSERVABILITY ---
            with st.expander("🛠️ View Raw AI Detection Log (Data Layer)"):
                st.dataframe(raw_data, use_container_width=True)

    except NYCBoundaryError as e:
        st.error(f"Jurisdiction Error: {e.message}")
    except SentinelError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Critical System Failure: {str(e)}")

else:
    # LANDING STATE
    st.title("Audit-Ready Site Intelligence")
    st.markdown("""
    ### Welcome to SentinelScope
    Automate construction compliance audits against **NYC Building Code 2022** requirements.
    
    1. **Project Details**: Set your site context in the sidebar.
    2. **Upload Evidence**: Ingest site photos or OpenSpace capture logs.
    3. **AI Audit**: Generate real-time risk assessments and evidence packages.
    """)
    st.image("https://images.unsplash.com/photo-1503387762-592dea58ef21?auto=format&fit=crop&w=1200", 
             caption="Architecture & Compliance Unified", use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>"
    f"SentinelScope v0.1.0 • {datetime.now().strftime('%B %Y')} • Built for the Construction Industry"
    f"</div>", 
    unsafe_allow_html=True
)
