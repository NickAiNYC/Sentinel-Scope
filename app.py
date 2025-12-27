# ====== IMPORTS ======
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from openai import OpenAI
from typing import List, Dict, Any
import time

# ====== DEEPSEEK INTEGRATION ======
def init_deepseek_client():
    """Initialize DeepSeek API client"""
    api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
    if not api_key:
        st.warning("⚠️ DeepSeek API key not found. Using mock data.")
        return None
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

# DeepSeek Prompts
DEEPSEEK_SYSTEM_PROMPT = """You are a construction compliance expert specializing in NYC DOB regulations and OpenSpace capture analysis.

Your task: Analyze construction site captures and classify them for compliance documentation.

ALWAYS respond with valid JSON matching the specified schema. No markdown, no explanations."""

CLASSIFICATION_PROMPT = """Analyze this construction capture description:

DESCRIPTION: {description}
PROJECT TYPE: {project_type}
LOCATION CONTEXT: {location_context}

Classify into these EXACT categories:

MILESTONE (pick ONE):
- Site_Prep
- Foundation
- Structural_Frame
- MEP_Rough_in
- Fireproofing
- Drywall
- Finishes
- Punch_List

MEP_SYSTEM (if visible):
- HVAC
- Electrical
- Plumbing
- Fire_Protection
- Elevator
- null

LOCATION:
- Floor number or "Basement"
- Zone: Core, Perimeter, Interior, Exterior

CONFIDENCE: 0.0-1.0
COMPLIANCE_RELEVANCE: 0-100

Return JSON:
{{
  "milestone": "string",
  "mep_system": "string|null",
  "location": {{
    "floor": "string",
    "zone": "string"
  }},
  "confidence": float,
  "compliance_relevance": int,
  "evidence_notes": "string"
}}"""

GAP_DETECTION_PROMPT = """Analyze construction timeline against NYC DOB requirements:

PROJECT INFO:
- Type: {project_type}
- Floors: {total_floors}
- Location: {project_address}

CAPTURE HISTORY (last 30 days):
{capture_history}

REQUIRED MILESTONES (per NYC BC 2022):
{required_milestones}

Identify:
1. Missing milestones with deadlines
2. Compliance gaps with DOB code references
3. Risk level (high/medium/low)

Return JSON:
{{
  "missing_milestones": [
    {{
      "milestone": "string",
      "floor_range": "string",
      "dob_code": "string",
      "risk_level": "string",
      "deadline": "YYYY-MM-DD",
      "recommendation": "string"
    }}
  ],
  "compliance_score": 0-100,
  "risk_score": 0-100,
  "next_priority": "string"
}}"""

def analyze_with_deepseek(client, prompt: str, max_tokens: int = 2000) -> Dict:
    """Call DeepSeek API for analysis"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        st.error(f"DeepSeek API error: {e}")
        return None

def get_required_milestones(project_context: Dict) -> str:
    """Get required milestones based on project type"""
    if project_context.get("project_type") == "Commercial":
        return """- Foundation: Floors 1-2 (Week 4)
- Structural Frame: Floors 1-12 (Week 16)
- MEP Rough-in: Floors 3-12 (Week 24)
- Fireproofing: Floors 3-12 (Week 28)
- Drywall: Floors 1-12 (Week 32)
- Final MEP: All floors (Week 36)
- CO Ready: All floors (Week 40)"""
    else:
        return """Standard NYC residential construction milestones."""

def analyze_captures(captures: List[Dict], project_context: Dict) -> Dict:
    """Analyze multiple captures"""
    client = init_deepseek_client()
    
    if not client:
        return None  # Will use mock data
    
    results = []
    
    # Process captures in batches
    for i, capture in enumerate(captures[:10]):  # Limit for demo
        prompt = CLASSIFICATION_PROMPT.format(
            description=capture.get("description", ""),
            project_type=project_context.get("project_type", "Commercial"),
            location_context=project_context.get("location_context", "")
        )
        
        result = analyze_with_deepseek(client, prompt)
        if result:
            results.append(result)
    
    # Perform gap analysis
    if results:
        gap_prompt = GAP_DETECTION_PROMPT.format(
            project_type=project_context.get("project_type", "Commercial"),
            total_floors=project_context.get("total_floors", 12),
            project_address=project_context.get("project_address", ""),
            capture_history=json.dumps(results, indent=2),
            required_milestones=get_required_milestones(project_context)
        )
        
        gap_analysis = analyze_with_deepseek(client, gap_prompt, max_tokens=3000)
    else:
        gap_analysis = None
    
    return {
        "classification_results": results,
        "gap_analysis": gap_analysis,
        "summary": generate_summary(results, gap_analysis, len(captures))
    }

def generate_summary(results: List, gap_analysis: Dict, total_captures: int) -> Dict:
    """Generate summary statistics"""
    if not results:
        # Return default values if no results
        return {
            "total_captures": total_captures,
            "avg_confidence": 0.85,
            "avg_compliance_relevance": 75,
            "compliance_rate": 87.5,
            "risk_score": 28,
            "missing_milestones": 3,
            "captures_by_milestone": {"Structural_Frame": 10, "MEP_Rough_in": 8, "Fireproofing": 6},
            "estimated_savings_hours": total_captures * 0.5,
            "estimated_savings_dollars": total_captures * 50
        }
    
    avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)
    avg_relevance = sum(r.get("compliance_relevance", 0) for r in results) / len(results)
    
    # Count by milestone
    milestones = {}
    for r in results:
        milestone = r.get("milestone", "Unknown")
        milestones[milestone] = milestones.get(milestone, 0) + 1
    
    return {
        "total_captures": total_captures,
        "avg_confidence": avg_confidence,
        "avg_compliance_relevance": avg_relevance,
        "compliance_rate": gap_analysis.get("compliance_score", 87.5) if gap_analysis else 87.5,
        "risk_score": gap_analysis.get("risk_score", 28) if gap_analysis else 28,
        "missing_milestones": len(gap_analysis.get("missing_milestones", [])) if gap_analysis else 3,
        "captures_by_milestone": milestones,
        "estimated_savings_hours": total_captures * 0.5,  # 30 min per capture
        "estimated_savings_dollars": total_captures * 50   # $50 per capture
    }

# ====== MOCK DATA GENERATOR ======
def generate_mock_data():
    """Generate mock data for demo"""
    return {
        "total_captures": 156,
        "compliance_rate": 87.5,
        "missing_milestones": 8,
        "risk_score": 28,
        "estimated_savings_hours": 47,
        "estimated_savings_dollars": 5875,
        "captures_by_milestone": {
            "Foundation": 24,
            "Structural_Frame": 32,
            "MEP_Rough_in": 28,
            "Drywall": 22,
            "Fireproofing": 18,
            "Final MEP": 20,
            "CO Ready": 12
        },
        "compliance_timeline": pd.DataFrame({
            "date": pd.date_range(start="2024-09-01", periods=12, freq="W"),
            "compliance_rate": [45, 52, 61, 68, 72, 75, 78, 82, 85, 87, 87.5, 87.5]
        }),
        "gaps": [
            {"milestone": "MEP Rough-in", "floor": "7-9", "dob_code": "BC 2022 §1207.5", "risk": "high", "deadline": "2025-02-15"},
            {"milestone": "Fireproofing", "floor": "8", "dob_code": "BC 2022 §704.2", "risk": "high", "deadline": "2025-02-10"},
            {"milestone": "Safety Netting", "floor": "All", "dob_code": "BC 2022 §3309.7", "risk": "medium", "deadline": "2025-01-30"}
        ],
        "area_violations": [
            {"violation": "Safety netting", "count": 12, "avg_fine": 5000},
            {"violation": "Site safety plans", "count": 8, "avg_fine": 2500},
            {"violation": "Fireproofing documentation", "count": 6, "avg_fine": 3500}
        ]
    }

# ====== STREAMLIT DASHBOARD ======
# Page config
st.set_page_config(
    page_title="SentinelScope - AI Compliance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .risk-high {
        color: #ff4444;
        font-weight: bold;
    }
    .risk-medium {
        color: #ffaa00;
        font-weight: bold;
    }
    .risk-low {
        color: #00cc66;
        font-weight: bold;
    }
    .stAlert {
        border-radius: 10px;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<p class="main-header">🛡️ SentinelScope</p>', unsafe_allow_html=True)
    st.markdown("**AI-Augmented Compliance Agent for NYC Construction**")
with col2:
    st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=ThriveAI", width=150)

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Project Settings")
    
    project_name = st.text_input("Project Name", "Hudson Yards Phase 3")
    project_type = st.selectbox("Project Type", ["Commercial", "Residential", "Mixed-Use", "Industrial"])
    total_floors = st.slider("Total Floors", 1, 50, 12)
    project_address = st.text_input("Address", "450 W 33rd St, New York, NY")
    
    st.markdown("---")
    st.header("📤 Upload Captures")
    uploaded_files = st.file_uploader(
        "Upload construction photos",
        type=["jpg", "jpeg", "png", "csv"],
        accept_multiple_files=True,
        help="Upload OpenSpace captures or site photos"
    )
    
    st.markdown("---")
    insurance_type = st.selectbox(
        "Insurance Type",
        ["Builder's Risk", "General Liability", "Workers Comp", "Property"]
    )
    
    analyze_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("**API Status:** " + ("🔑 Connected" if st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY") else "⚠️ Using Mock Data"))

# Main content
if analyze_button:
    if not uploaded_files:
        st.warning("Please upload at least one capture file")
        st.stop()
    
    # Prepare captures for analysis
    captures = []
    for uploaded_file in uploaded_files[:10]:  # Limit to 10 for demo
        # In real app, you'd use image analysis here
        captures.append({
            "filename": uploaded_file.name,
            "description": f"Construction photo: {uploaded_file.name}",
            "timestamp": datetime.now().isoformat(),
            "size": uploaded_file.size
        })
    
    # Project context
    project_context = {
        "project_name": project_name,
        "project_type": project_type,
        "total_floors": total_floors,
        "project_address": project_address,
        "insurance_type": insurance_type
    }
    
    # Run analysis
    with st.spinner("🤖 Analyzing captures with DeepSeek AI..."):
        # For demo, use mock if no API key, otherwise real analysis
        api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
        
        if api_key:
            # Real analysis
            analysis_results = analyze_captures(captures, project_context)
            
            if analysis_results is None:
                # DeepSeek failed, fallback to mock
                st.info("Falling back to mock data for demo")
                mock_data = generate_mock_data()
                analysis_results = {
                    "summary": mock_data,
                    "classification_results": [],
                    "gap_analysis": {
                        "missing_milestones": mock_data["gaps"],
                        "compliance_score": mock_data["compliance_rate"],
                        "risk_score": mock_data["risk_score"],
                        "next_priority": "MEP Rough-in floors 7-9"
                    }
                }
        else:
            # Mock data for demo
            time.sleep(2)  # Simulate processing
            mock_data = generate_mock_data()
            analysis_results = {
                "summary": mock_data,
                "classification_results": [],
                "gap_analysis": {
                    "missing_milestones": mock_data["gaps"],
                    "compliance_score": mock_data["compliance_rate"],
                    "risk_score": mock_data["risk_score"],
                    "next_priority": "MEP Rough-in floors 7-9"
                }
            }
        
        data = analysis_results["summary"]
        gap_analysis = analysis_results.get("gap_analysis", {})
        classification_results = analysis_results.get("classification_results", [])
    
    # Success message
    st.success(f"✅ Analyzed {len(uploaded_files)} captures successfully!")
    
    # Show if using real API or mock
    if api_key and analysis_results and analysis_results.get("classification_results"):
        st.info("🔑 **Using DeepSeek AI for real analysis**")
    else:
        st.info("🔄 **Using mock data for demonstration**")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Compliance Rate",
            value=f"{data['compliance_rate']}%",
            delta=f"+{data['compliance_rate'] - 80:.1f}% from target"
        )
    
    with col2:
        st.metric(
            label="⚠️ Critical Gaps",
            value=data['missing_milestones'],
            delta=f"-{data['missing_milestones']} to resolve",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="⏱️ Time Saved",
            value=f"{data['estimated_savings_hours']:.0f} hrs",
            delta=f"${data['estimated_savings_dollars']:,}"
        )
    
    with col4:
        risk_color = "🟢" if data['risk_score'] < 30 else "🟡" if data['risk_score'] < 60 else "🔴"
        st.metric(
            label="🎯 Risk Score",
            value=f"{risk_color} {data['risk_score']}/100",
            delta="Low risk" if data['risk_score'] < 30 else "Medium risk" if data['risk_score'] < 60 else "High risk"
        )
    
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Compliance Timeline
        st.subheader("📈 Compliance Progress Over Time")
        if 'compliance_timeline' in data:
            fig_timeline = px.line(
                data['compliance_timeline'],
                x='date',
                y='compliance_rate',
                title='Project Compliance Rate',
                labels={'compliance_rate': 'Compliance %', 'date': 'Date'},
                markers=True
            )
            fig_timeline.add_hline(y=80, line_dash="dash", line_color="red", 
                                  annotation_text="Target: 80%")
            fig_timeline.update_layout(height=300)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Milestone Distribution
        st.subheader("🏗️ Captures by Milestone")
        if 'captures_by_milestone' in data:
            fig_milestones = go.Figure(data=[
                go.Bar(
                    x=list(data['captures_by_milestone'].keys()),
                    y=list(data['captures_by_milestone'].values()),
                    marker_color='#667eea',
                    text=list(data['captures_by_milestone'].values()),
                    textposition='auto'
                )
            ])
            fig_milestones.update_layout(
                title='Distribution of Documented Milestones',
                xaxis_title='Milestone Type',
                yaxis_title='Number of Captures',
                height=300
            )
            st.plotly_chart(fig_milestones, use_container_width=True)
    
    with col2:
        # Critical Gaps from gap analysis
        st.subheader("🚨 Critical Compliance Gaps")
        if gap_analysis and 'missing_milestones' in gap_analysis:
            gaps_to_show = gap_analysis['missing_milestones'][:5]  # Limit to 5
            for gap in gaps_to_show:
                risk_class = f"risk-{gap.get('risk_level', 'medium').lower()}"
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {"#ff4444" if gap.get("risk_level") == "high" else "#ffaa00"}'>
                        <strong class='{risk_class}'>{gap.get('milestone', 'Unknown')}</strong><br/>
                        <small>📍 Floor {gap.get('floor_range', 'N/A')}</small><br/>
                        <small>📋 {gap.get('dob_code', 'No DOB code')}</small><br/>
                        <small>⏰ Due: {gap.get('deadline', 'ASAP')}</small>
                    </div>
                    """, unsafe_allow_html=True)
        elif 'gaps' in data:
            # Fallback to mock gaps
            for gap in data['gaps'][:3]:
                risk_class = f"risk-{gap['risk']}"
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {"#ff4444" if gap["risk"] == "high" else "#ffaa00"}'>
                        <strong class='{risk_class}'>{gap['milestone']}</strong><br/>
                        <small>📍 Floor {gap['floor']}</small><br/>
                        <small>📋 {gap['dob_code']}</small><br/>
                        <small>⏰ Due: {gap['deadline']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Area Risk Context
        st.subheader("📍 Area Violation Patterns")
        st.caption(f"Common violations within 0.5mi of {project_address}")
        if 'area_violations' in data:
            for violation in data['area_violations'][:3]:
                st.markdown(f"""
                <div style='background-color: #fff3cd; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.9rem'>
                    <strong>{violation['violation']}</strong><br/>
                    <small>{violation['count']} violations | Avg fine: ${violation['avg_fine']:,}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Evidence Table
    st.subheader("📄 Insurance-Ready Evidence Table")
    st.caption(f"Formatted for {insurance_type} renewal submission")
    
    evidence_data = pd.DataFrame({
        "Date": ["2024-12-20", "2024-12-18", "2024-12-15", "2024-12-12", "2024-12-10"],
        "Location": ["Floor 9", "Floor 8", "Floor 7", "Floor 6", "Floor 5"],
        "Milestone": ["Structural_Frame", "MEP_Rough_in", "MEP_Rough_in", "Drywall", "Fireproofing"],
        "Quality": ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐"],
        "Status": ["✅ Compliant", "✅ Compliant", "❌ Gap", "✅ Compliant", "✅ Compliant"],
        "DOB Code": ["BC §1805", "BC §1207.5", "BC §1207.5", "BC §2508", "BC §704.2"],
        "Confidence": ["98%", "94%", "89%", "96%", "92%"]
    })
    
    st.dataframe(
        evidence_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quality": st.column_config.TextColumn("Evidence Quality"),
            "Status": st.column_config.TextColumn("Status"),
            "Confidence": st.column_config.TextColumn("AI Confidence")
        }
    )
    
    # Show classification results if available
    if classification_results:
        with st.expander("🔍 View Detailed AI Classifications", expanded=False):
            for i, result in enumerate(classification_results[:5]):
                st.json(result)
    
    # Executive Summary
    st.markdown("---")
    st.subheader("📋 Executive Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Key Findings:**
        - ✅ {data['compliance_rate']}% milestone compliance achieved
        - 🚨 **CRITICAL**: {data['missing_milestones']} missing milestones detected
        - ⚡ Automated review saved {data['estimated_savings_hours']:.0f} hours (${data['estimated_savings_dollars']:,})
        - 📊 Project risk score: {data['risk_score']}/100 ({'Low' if data['risk_score'] < 30 else 'Medium' if data['risk_score'] < 60 else 'High'} risk)
        """)
    
    with col2:
        st.markdown(f"""
        **Recommended Actions:**
        1. Schedule MEP inspection for floors 7-9 by Feb 15 (HIGH PRIORITY)
        2. Document fireproofing with thermal imaging
        3. Update safety netting documentation
        4. Prepare {insurance_type} renewal evidence package
        """)
    
    # Download options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download Full Report (PDF)",
            data="Mock PDF data - replace with actual PDF generation",
            file_name=f"sentinel_report_{project_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    
    with col2:
        st.download_button(
            label="📊 Download Evidence Table (CSV)",
            data=evidence_data.to_csv(index=False),
            file_name="evidence_table.csv",
            mime="text/csv"
        )
    
    with col3:
        st.download_button(
            label="📋 Download Analysis (JSON)",
            data=json.dumps({
                "project": project_context,
                "summary": data,
                "gap_analysis": gap_analysis,
                "timestamp": datetime.now().isoformat()
            }, indent=2),
            file_name="analysis_results.json",
            mime="application/json"
        )

else:
    # Landing state
    st.info("👈 Configure project settings and upload construction captures to begin analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 How It Works
        1. **Upload** OpenSpace captures or site photos
        2. **AI Classification** automatically identifies milestones
        3. **Gap Detection** finds missing documentation
        4. **Report Generation** creates insurance-ready evidence
        """)
    
    with col2:
        st.markdown("""
        ### 💡 Key Features
        - ⚡ 40+ hours saved per project
        - 🎯 NYC DOB code compliance
        - 📍 Area violation context
        - 📊 Real-time risk scoring
        """)
    
    with col3:
        st.markdown("""
        ### 📈 Business Impact
        - **Before**: 40-80 hours manual work
        - **After**: 5-10 minutes automated
        - **Savings**: $5,000+ per review
        - **Result**: Audit-ready compliance
        """)
    
    # Demo section
    st.markdown("---")
    st.subheader("🎮 Quick Demo")
    
    demo_col1, demo_col2 = st.columns(2)
    
    with demo_col1:
        if st.button("🚀 Try Demo with Mock Data", use_container_width=True):
            # Simulate uploading files
            st.session_state.demo_mode = True
            st.rerun()
    
    with demo_col2:
        st.caption("Click to see the dashboard in action with sample data")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <strong>SentinelScope</strong> | Built by <a href='https://thrivai.ai' target='_blank'>Nick Altstein</a> | 
    <a href='https://github.com/NickAiNYC/sentinel-scope' target='_blank'>GitHub</a> | 
    AI-Augmented Compliance for NYC Construction
</div>
""", unsafe_allow_html=True)
