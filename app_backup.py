"""
Streamlit dashboard for SentinelScope - Construction Compliance AI
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add core directory to path
sys.path.append('core')

st.set_page_config(
    page_title="SentinelScope | Construction Compliance AI",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        color: #1e40af;
        margin-bottom: 0;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .risk-high { color: #dc2626; font-weight: bold; }
    .risk-medium { color: #ea580c; font-weight: bold; }
    .risk-low { color: #16a34a; font-weight: bold; }
    .stButton button {
        background-color: #1e40af;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🛡️ SentinelScope</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">LLM Agent for NYC Construction Compliance</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    project_type = st.selectbox(
        "Project Type",
        ["structural", "mep", "interior", "commercial"],
        help="Select the type of construction project"
    )
    
    st.header("📊 Analysis Options")
    enable_gap_analysis = st.checkbox("Enable Gap Analysis", value=True)
    enable_dob_alerts = st.checkbox("Enable DOB Alerts", value=False, 
                                    help="NYC DOB violation alerts (mock data for now)")
    
    st.header("ℹ️ About")
    st.info("""
    **SentinelScope** automates construction compliance:
    1. Classifies OpenSpace captures
    2. Detects missing milestones
    3. Generates evidence reports
    4. Monitors DOB risks
    """)

# Main content
st.header("📤 Upload Construction Data")
uploaded_file = st.file_uploader(
    "Upload CSV file with construction captures",
    type=['csv'],
    help="Expected columns: date, description, image_path"
)

if uploaded_file:
    # Load data
    df = pd.read_csv(uploaded_file)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"✅ Successfully loaded {len(df)} records")
    with col2:
        if st.button("🚀 Run Full Analysis", type="primary"):
            st.session_state.analyze = True
    
    with st.expander("📋 Data Preview", expanded=True):
        st.dataframe(df, width='stretch')
    
    # Run analysis if requested
    if st.session_state.get('analyze', False):
        with st.spinner("Analyzing construction data..."):
            try:
                # Import modules
                from classifier import batch_classify
                from gap_detector import detect_gaps
                from report import generate_evidence_table
                from dob_alerts import get_dob_alerts
                
                # 1. Classify data
                classified_df = batch_classify(df)
                
                # 2. Detect gaps
                if enable_gap_analysis:
                    milestones = classified_df['milestone'].tolist()
                    gap_analysis = detect_gaps(milestones, project_type)
                
                # 3. Generate report
                report_text = generate_evidence_table(classified_df, gap_analysis)
                
                # 4. Get DOB alerts (if enabled)
                dob_data = None
                if enable_dob_alerts:
                    dob_data = get_dob_alerts(40.6782, -73.9442)  # Mock NYC coordinates
                
                # Display results in tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Evidence", 
                    "⚠️ Gap Analysis", 
                    "🗺️ DOB Alerts", 
                    "📄 Full Report"
                ])
                
                with tab1:
                    st.subheader("Classified Evidence")
                    st.dataframe(classified_df, width='stretch')
                
                with tab2:
                    if enable_gap_analysis:
                        st.subheader("Compliance Analysis")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Coverage", f"{gap_analysis['coverage_percentage']}%")
                        with col2:
                            st.metric("Missing Milestones", gap_analysis['gap_count'])
                        with col3:
                            risk_class = gap_analysis['risk_level'].split()[1].lower()
                            st.markdown(f'<div class="risk-{risk_class}">{gap_analysis["risk_level"]}</div>', 
                                      unsafe_allow_html=True)
                        
                        # Missing milestones
                        if gap_analysis['missing_milestones']:
                            st.error("**Missing Required Documentation:**")
                            for item in gap_analysis['missing_milestones']:
                                st.write(f"- {item}")
                        else:
                            st.success("✅ All required milestones documented!")
                    else:
                        st.info("Gap analysis disabled")
                
                with tab3:
                    if enable_dob_alerts and dob_data:
                        st.subheader("NYC DOB Risk Assessment")
                        st.metric("Total Violations", dob_data['total_alerts'])
                        st.metric("High Risk", dob_data['high_risk_count'])
                        st.write(f"**Risk Level:** {dob_data['risk_level']}")
                        
                        st.subheader("Recent Alerts")
                        for alert in dob_data['alerts']:
                            with st.expander(f"{alert['date']} - {alert['violation_type']}"):
                                st.write(f"Address: {alert['address']}")
                                st.write(f"Status: {alert['status']}")
                                st.write(f"Distance: {alert['distance_m']}m")
                    else:
                        st.info("DOB alerts disabled or no data available")
                        st.caption("Real NYC DOB API integration coming in Day 4")
                
                with tab4:
                    st.subheader("Complete Evidence Report")
                    st.markdown(report_text)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Report (Markdown)",
                        data=report_text,
                        file_name="sentinel_report.md",
                        mime="text/markdown"
                    )
                
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")
                st.exception(e)
        
        # Reset analysis flag
        st.session_state.analyze = False
    
else:
    # Show sample data and instructions
    st.info("👆 Upload a CSV file to begin analysis")
    
    with st.expander("📝 Sample CSV Format & Data"):
        st.code("""date,description,image_path
2025-01-15,MEP rough-in inspection floor 5,captures/mep_floor5.jpg
2025-01-10,Structural steel installation floor 4,captures/steel_floor4.jpg
2025-01-05,Fireproofing application columns,captures/fireproof_col.jpg""")
        
        # Load and show sample data
        if os.path.exists('data/mock_frames.csv'):
            sample_df = pd.read_csv('data/mock_frames.csv')
            st.write("**Sample Data Preview:**")
            st.dataframe(sample_df)
            
            if st.button("Try with Sample Data"):
                # Simulate upload
                uploaded_file = True
                df = sample_df.copy()

# Footer
st.markdown("---")
st.caption("SentinelScope v0.1 | Day 1 MVP | Built by Nick Altstein | NYC")
st.caption("Next: Day 2 - Enhanced gap detection and proof tables")
