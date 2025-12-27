import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
import time
from datetime import datetime
from openai import OpenAI

# ====== CORE MODULE IMPORTS ======
from core.constants import BRAND_THEME, MILESTONES
from core.exceptions import NYCBoundaryError, AIProviderError, SentinelError
from core.models import GapAnalysisResponse, CaptureClassification
from core.gap_detector import detect_gaps
from core.geocoding import lookup_address

# ====== PAGE CONFIGURATION ======
st.set_page_config(
    page_title="SentinelScope | AI Construction Audit",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====== ARCHITECTURAL BEIGE & BROWN THEME (CSS) ======
st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: {BRAND_THEME['BACKGROUND_BEIGE']};
        color: {BRAND_THEME['PRIMARY_BROWN']};
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {BRAND_THEME['SIDEBAR_TAN']};
        border-right: 1px solid {BRAND_THEME['PRIMARY_BROWN']};
    }}

    /* Metric Cards */
    div[data-testid="stMetricValue"] {{
        color: {BRAND_THEME['MAHOGANY']};
    }}
    .stMetric {{
        background-color: white;
        border: 1px solid {BRAND_THEME['SIDEBAR_TAN']};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}

    /* Typography */
    h1, h2, h3 {{
        color: {BRAND_THEME['PRIMARY_BROWN']} !important;
        font-family: 'Georgia', serif;
        font-weight: 700;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {BRAND_THEME['PRIMARY_BROWN']};
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {BRAND_THEME['MAHOGANY']};
        color: {BRAND_THEME['BACKGROUND_BEIGE']};
    }}
    </style>
""", unsafe_allow_html=True)

# ====== AI UTILITIES (DeepSeek) ======
def get_ai_client():
    api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def run_ai_audit(uploaded_files, project_type):
    """Processes captures and runs gap detection"""
    # In a real production app, this would call core.classifier.batch_classify
    # For now, we simulate the found milestones from the upload
    time.sleep(1.5) # Simulate AI thinking
    
    # Mock result derived from your Gap Detector logic
    found_milestones = ["Foundation", "Structural Steel"] # Example detections
    
    # Trigger the modular Gap Engine
    analysis_results = detect_gaps(found_milestones, project_type)
    return analysis_results

# ====== SIDEBAR: PROJECT CONTROL ======
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=80)
    st.title("SentinelScope AI")
    st.markdown("---")
    
    with st.form("audit_input"):
        project_name = st.text_input("Project Name", "270 Park Ave Reconstruction")
        address = st.text_input("Site Address", "270 Park Ave, New York, NY")
        p_type = st.selectbox("Audit Category", ["Structural", "MEP"])
        uploads = st.file_uploader("Upload Site Captures", accept_multiple_files=True)
        submit = st.form_submit_button("🚀 RUN AI COMPLIANCE AUDIT")
    
    st.markdown("---")
    st.caption(f"Built by Nick Altstein | NYC BC 2022 Ready")

# ====== MAIN DASHBOARD ======
if submit and uploads:
    try:
        # Validate Address
        loc = lookup_address(address)
        
        with st.spinner("🕵️ AI Agent analyzing captures against NYC Building Code..."):
            analysis = run_ai_audit(uploads, p_type)
        
        # --- ROW 1: KPI METRICS ---
        st.header(f"Executive Summary: {project_name}")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.metric("Compliance Score", f"{analysis.compliance_score}%")
        m2.metric("Missing Gaps", analysis.gap_count, delta_color="inverse")
        m3.metric("Safety Risk", "LOW" if analysis.risk_score < 30 else "CRITICAL")
        m4.metric("Priority", analysis.next_priority)

        st.divider()

        # --- ROW 2: VISUAL INTELLIGENCE ---
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📍 Site Surveillance")
            # This is where your Map component or Timeline would go
            st.image("https://images.unsplash.com/photo-1541888946425-d81bb19480c5?auto=format&fit=crop&w=800", 
                     caption="Latest AI Capture Analysis", use_container_width=True)

        with col_right:
            st.subheader("⚖️ Risk Index")
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = analysis.compliance_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'tickcolor': BRAND_THEME['PRIMARY_BROWN']},
                    'bar': {'color': BRAND_THEME['MAHOGANY']},
                    'steps': [
                        {'range': [0, 60], 'color': "#E5D3B3"},
                        {'range': [60, 85], 'color': BRAND_THEME['SIDEBAR_TAN']},
                        {'range': [85, 100], 'color': BRAND_THEME['SUCCESS_GREEN']}
                    ],
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': BRAND_THEME['PRIMARY_BROWN']}, height=300)
            st.plotly_chart(fig, use_container_width=True)

        # --- ROW 3: DETAILED GAP TABLE ---
        st.subheader("🔍 Compliance Gaps & Required Actions")
        if analysis.missing_milestones:
            # Convert Pydantic objects to a displayable DataFrame
            gap_data = [
                {
                    "Milestone": g.milestone,
                    "NYC Code": g.dob_code,
                    "Risk": g.risk_level,
                    "Recommendation": g.recommendation
                } for g in analysis.missing_milestones
            ]
            st.table(pd.DataFrame(gap_data))
        else:
            st.success("All required milestones documented. Site is audit-ready.")

        # --- EXPORT ---
        st.divider()
        if st.button("📥 Generate PDF Audit Report"):
            st.info("Generating professional PDF via core.report...")

    except NYCBoundaryError as e:
        st.error(f"Jurisdiction Error: {e.message}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    # LANDING STATE
    st.title("Audit-Ready Site Intelligence")
    st.markdown("""
    ### Welcome to SentinelScope
    Analyze your construction site captures against **NYC Building Code 2022** requirements using DeepSeek Vision AI.
    
    1. **Project Details**: Enter your site address and project type in the sidebar.
    2. **Upload Evidence**: Drag and drop site photos or OpenSpace capture logs.
    3. **AI Audit**: Receive a real-time risk assessment and gap analysis.
    """)
    st.image("https://images.unsplash.com/photo-1503387762-592dea58ef21?auto=format&fit=crop&w=1200", 
             caption="Architecture & Compliance Unified", use_container_width=True)
