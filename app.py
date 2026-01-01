import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# ====== PAGE CONFIG ======
st.set_page_config(
    page_title="SentinelScope Pro | Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====== CUSTOM CSS ======
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Professional color scheme */
    :root {
        --primary: #1e40af;
        --success: #059669;
        --warning: #d97706;
        --danger: #dc2626;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary);
    }
    
    .risk-critical {
        border-left-color: var(--danger);
        background: #fef2f2;
    }
    
    .risk-warning {
        border-left-color: var(--warning);
        background: #fffbeb;
    }
    
    .risk-safe {
        border-left-color: var(--success);
        background: #f0fdf4;
    }
    
    /* Professional headers */
    .dashboard-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    /* Data tables */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-active {
        background: #dcfce7;
        color: #166534;
    }
    
    .status-delayed {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #92400e;
    }
</style>
""", unsafe_allow_html=True)

# ====== SESSION STATE INITIALIZATION ======
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'overview'
if 'projects' not in st.session_state:
    # Sample data - replace with database later
    st.session_state.projects = [
        {
            'id': 'proj_001',
            'name': '270 Park Avenue',
            'address': '270 Park Ave, Manhattan, NY 10017',
            'type': 'Commercial High-Rise',
            'status': 'active',
            'compliance_score': 87,
            'risk_score': 23,
            'start_date': '2024-03-15',
            'target_completion': '2026-08-30',
            'total_captures': 1247,
            'open_gaps': 3,
            'last_audit': '2024-12-28',
            'value': 850000000,
            'gc_firm': 'Turner Construction',
            'insurance_premium': 1200000
        },
        {
            'id': 'proj_002',
            'name': 'Hudson Yards Phase 3',
            'address': '500 W 33rd St, Manhattan, NY 10001',
            'type': 'Mixed-Use Development',
            'status': 'active',
            'compliance_score': 92,
            'risk_score': 12,
            'start_date': '2024-01-10',
            'target_completion': '2025-12-15',
            'total_captures': 2891,
            'open_gaps': 1,
            'last_audit': '2024-12-30',
            'value': 1200000000,
            'gc_firm': 'Tishman Construction',
            'insurance_premium': 1800000
        },
        {
            'id': 'proj_003',
            'name': 'Brooklyn Navy Yard Expansion',
            'address': '63 Flushing Ave, Brooklyn, NY 11205',
            'type': 'Industrial Renovation',
            'status': 'delayed',
            'compliance_score': 68,
            'risk_score': 45,
            'start_date': '2024-05-20',
            'target_completion': '2025-11-30',
            'total_captures': 567,
            'open_gaps': 8,
            'last_audit': '2024-12-15',
            'value': 125000000,
            'gc_firm': 'Skanska USA',
            'insurance_premium': 450000
        }
    ]

# ====== TOP NAVIGATION BAR ======
col_logo, col_nav1, col_nav2, col_nav3, col_nav4, col_user = st.columns([1.5, 1, 1, 1, 1, 1.5])

with col_logo:
    st.markdown("### 🏗️ **SentinelScope Pro**")

nav_buttons = [
    ('overview', '📊 Overview', col_nav1),
    ('projects', '🏗️ Projects', col_nav2),
    ('analytics', '📈 Analytics', col_nav3),
    ('compliance', '⚖️ Compliance', col_nav4)
]

for view_key, label, col in nav_buttons:
    with col:
        if st.button(label, key=f"nav_{view_key}", use_container_width=True,
                    type="primary" if st.session_state.current_view == view_key else "secondary"):
            st.session_state.current_view = view_key
            st.rerun()

with col_user:
    st.markdown("**👤 John Smith**  \n*Senior PM*")

st.markdown("---")

# ====== DASHBOARD VIEWS ======

# ---------------- OVERVIEW VIEW ----------------
if st.session_state.current_view == 'overview':
    
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1 style='margin:0;'>Portfolio Command Center</h1>
        <p style='margin:0.5rem 0 0 0; opacity:0.9;'>Real-time compliance intelligence across all NYC projects</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_projects = len(st.session_state.projects)
    active_projects = len([p for p in st.session_state.projects if p['status'] == 'active'])
    avg_compliance = sum(p['compliance_score'] for p in st.session_state.projects) / total_projects
    total_gaps = sum(p['open_gaps'] for p in st.session_state.projects)
    total_value = sum(p['value'] for p in st.session_state.projects)
    
    with col1:
        st.metric("Active Projects", f"{active_projects}/{total_projects}")
    with col2:
        st.metric("Avg Compliance", f"{avg_compliance:.0f}%", 
                 delta=f"+{avg_compliance-85:.0f}%" if avg_compliance > 85 else f"{avg_compliance-85:.0f}%")
    with col3:
        st.metric("Open Gaps", total_gaps, 
                 delta="-2 vs last week", delta_color="inverse")
    with col4:
        st.metric("Portfolio Value", f"${total_value/1e9:.1f}B")
    with col5:
        premium_at_risk = sum(p['insurance_premium'] * (p['risk_score']/100) for p in st.session_state.projects)
        st.metric("Premium at Risk", f"${premium_at_risk/1e6:.1f}M")
    
    st.markdown("---")
    
    # Two-column layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Project Status Table
        st.subheader("🏗️ Active Projects")
        
        df = pd.DataFrame(st.session_state.projects)
        
        # Format display
        display_df = df[['name', 'address', 'compliance_score', 'risk_score', 'open_gaps', 'status']].copy()
        display_df.columns = ['Project', 'Location', 'Compliance', 'Risk', 'Gaps', 'Status']
        
        # Add colored status badges
        def status_color(status):
            colors = {'active': '🟢', 'delayed': '🔴', 'pending': '🟡'}
            return f"{colors.get(status, '⚪')} {status.title()}"
        
        display_df['Status'] = display_df['Status'].apply(status_color)
        display_df['Compliance'] = display_df['Compliance'].apply(lambda x: f"{x}%")
        display_df['Risk'] = display_df['Risk'].apply(lambda x: f"⚠️ {x}" if x > 30 else f"{x}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Compliance Trend Chart
        st.subheader("📈 Compliance Trend (Last 30 Days)")
        
        # Generate sample trend data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        trend_data = []
        for project in st.session_state.projects[:3]:  # Top 3 projects
            scores = [project['compliance_score'] + (i % 5 - 2) for i in range(30)]
            for date, score in zip(dates, scores):
                trend_data.append({
                    'Date': date,
                    'Project': project['name'],
                    'Compliance Score': max(60, min(100, score))
                })
        
        trend_df = pd.DataFrame(trend_data)
        fig = px.line(trend_df, x='Date', y='Compliance Score', color='Project',
                     title="", height=300)
        fig.add_hline(y=85, line_dash="dash", line_color="red", 
                     annotation_text="Audit Threshold (85%)")
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        # Risk Distribution
        st.subheader("⚠️ Risk Distribution")
        
        risk_buckets = {
            'Low (0-25)': len([p for p in st.session_state.projects if p['risk_score'] <= 25]),
            'Medium (26-50)': len([p for p in st.session_state.projects if 25 < p['risk_score'] <= 50]),
            'High (51-75)': len([p for p in st.session_state.projects if 50 < p['risk_score'] <= 75]),
            'Critical (76+)': len([p for p in st.session_state.projects if p['risk_score'] > 75])
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(risk_buckets.keys()),
            values=list(risk_buckets.values()),
            hole=0.4,
            marker=dict(colors=['#059669', '#f59e0b', '#ef4444', '#7f1d1d'])
        )])
        fig.update_layout(showlegend=True, height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Priority Alerts
        st.subheader("🚨 Priority Alerts")
        
        high_risk_projects = [p for p in st.session_state.projects if p['risk_score'] > 30]
        
        for proj in high_risk_projects:
            risk_class = 'risk-critical' if proj['risk_score'] > 40 else 'risk-warning'
            st.markdown(f"""
            <div class="metric-card {risk_class}">
                <strong>{proj['name']}</strong><br>
                <small>{proj['open_gaps']} open gaps • Risk Score: {proj['risk_score']}</small>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        if st.button("➕ New Project Audit", use_container_width=True, type="primary"):
            st.session_state.current_view = 'new_audit'
            st.rerun()
        if st.button("📊 Export Portfolio Report", use_container_width=True):
            st.info("Generating comprehensive PDF report...")
        if st.button("📧 Send Weekly Summary", use_container_width=True):
            st.success("Weekly summary sent to team@gcfirm.com")

# ---------------- PROJECTS VIEW ----------------
elif st.session_state.current_view == 'projects':
    
    st.title("🏗️ Project Management")
    
    # Filter bar
    col_search, col_status, col_sort = st.columns([3, 1, 1])
    
    with col_search:
        search = st.text_input("🔍 Search projects", placeholder="Enter project name or address...")
    with col_status:
        status_filter = st.selectbox("Status", ["All", "Active", "Delayed", "Pending"])
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Compliance ↓", "Risk ↑", "Name", "Date"])
    
    st.markdown("---")
    
    # Project cards in grid
    projects = st.session_state.projects
    
    # Apply filters
    if status_filter != "All":
        projects = [p for p in projects if p['status'] == status_filter.lower()]
    if search:
        projects = [p for p in projects if search.lower() in p['name'].lower() or search.lower() in p['address'].lower()]
    
    # Grid layout (2 columns)
    cols_per_row = 2
    for i in range(0, len(projects), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(projects):
                proj = projects[i + j]
                with col:
                    # Project card
                    risk_class = 'risk-critical' if proj['risk_score'] > 40 else ('risk-warning' if proj['risk_score'] > 25 else 'risk-safe')
                    
                    st.markdown(f"""
                    <div class="metric-card {risk_class}">
                        <h3 style='margin:0 0 0.5rem 0;'>{proj['name']}</h3>
                        <p style='margin:0; color:#6b7280; font-size:0.875rem;'>{proj['address']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metrics
                    subcol1, subcol2, subcol3 = st.columns(3)
                    subcol1.metric("Compliance", f"{proj['compliance_score']}%")
                    subcol2.metric("Risk", proj['risk_score'])
                    subcol3.metric("Gaps", proj['open_gaps'])
                    
                    # Actions
                    if st.button("📊 View Details", key=f"view_{proj['id']}", use_container_width=True):
                        st.info(f"Opening detailed audit for {proj['name']}...")
                    
                    st.markdown("")

# ---------------- ANALYTICS VIEW ----------------
elif st.session_state.current_view == 'analytics':
    
    st.title("📈 Portfolio Analytics & Intelligence")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Financial Impact", "📊 Performance Metrics", "🎯 Predictive Insights", "📸 Photo Intelligence"])
    
    with tab1:
        st.subheader("Insurance Premium Optimization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Current vs Optimized Premium
            total_premium = sum(p['insurance_premium'] for p in st.session_state.projects)
            optimized_premium = total_premium * 0.85  # 15% savings potential
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Current Premium', 'Optimized Premium'],
                y=[total_premium/1e6, optimized_premium/1e6],
                marker_color=['#ef4444', '#059669'],
                text=[f"${total_premium/1e6:.1f}M", f"${optimized_premium/1e6:.1f}M"],
                textposition='outside'
            ))
            fig.update_layout(title="Potential Premium Savings", yaxis_title="Amount ($M)", height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.success(f"**Potential Annual Savings: ${(total_premium - optimized_premium)/1e6:.1f}M**")
        
        with col2:
            # Delay Cost Calculator
            st.markdown("**⏱️ Delay Cost Impact Calculator**")
            
            delay_days = st.slider("Project Delay (days)", 0, 30, 7)
            daily_cost = st.number_input("Daily Carrying Cost ($)", value=50000, step=10000)
            
            total_delay_cost = delay_days * daily_cost
            
            st.metric("Total Delay Cost", f"${total_delay_cost:,}", 
                     delta=f"-${total_delay_cost:,}" if delay_days == 0 else None,
                     delta_color="inverse")
            
            st.info(f"**Gap Resolution ROI:** Fixing compliance gaps prevents average {delay_days}-day delays, saving ${total_delay_cost:,}")
    
    with tab2:
        st.subheader("Portfolio Performance Benchmarking")
        
        # Compliance score distribution
        scores = [p['compliance_score'] for p in st.session_state.projects]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=scores,
            nbinsx=10,
            marker_color='#3b82f6',
            name='Projects'
        ))
        fig.add_vline(x=sum(scores)/len(scores), line_dash="dash", line_color="red",
                     annotation_text=f"Avg: {sum(scores)/len(scores):.0f}%")
        fig.update_layout(title="Compliance Score Distribution", xaxis_title="Score", yaxis_title="Count", height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Project type comparison
        st.subheader("Performance by Project Type")
        
        type_data = []
        for proj in st.session_state.projects:
            type_data.append({
                'Type': proj['type'],
                'Avg Compliance': proj['compliance_score'],
                'Avg Risk': proj['risk_score']
            })
        
        type_df = pd.DataFrame(type_data).groupby('Type').mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Compliance', x=type_df['Type'], y=type_df['Avg Compliance'], marker_color='#059669'))
        fig.add_trace(go.Bar(name='Risk', x=type_df['Type'], y=type_df['Avg Risk'], marker_color='#ef4444'))
        fig.update_layout(barmode='group', height=300, title="Compliance & Risk by Project Type")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("🔮 AI Predictive Insights")
        
        st.info("**Predictive Model:** Using historical data from 150+ NYC projects to forecast risks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Audit Likelihood Prediction**")
            
            for proj in st.session_state.projects[:3]:
                audit_prob = min(95, proj['risk_score'] * 1.5 + 20)
                color = "#ef4444" if audit_prob > 70 else ("#f59e0b" if audit_prob > 40 else "#059669")
                
                st.markdown(f"""
                <div style='padding:1rem; background:{color}22; border-left:4px solid {color}; border-radius:8px; margin-bottom:0.5rem;'>
                    <strong>{proj['name']}</strong><br>
                    <span style='font-size:1.5rem; font-weight:bold;'>{audit_prob:.0f}%</span> audit probability
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📅 Predicted Issue Timeline**")
            
            timeline_data = [
                {"Project": "270 Park Ave", "Issue": "Scaffolding inspection due", "Days": 14, "Priority": "Medium"},
                {"Project": "Hudson Yards", "Issue": "MEP rough-in review", "Days": 7, "Priority": "High"},
                {"Project": "Brooklyn Navy", "Issue": "Foundation photos missing", "Days": 3, "Priority": "Critical"}
            ]
            
            timeline_df = pd.DataFrame(timeline_data)
            
            for _, row in timeline_df.iterrows():
                priority_color = {"Critical": "#ef4444", "High": "#f59e0b", "Medium": "#3b82f6"}[row['Priority']]
                st.markdown(f"""
                <div style='padding:0.75rem; background:white; border-left:4px solid {priority_color}; border-radius:8px; margin-bottom:0.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.1);'>
                    <strong>{row['Project']}</strong><br>
                    {row['Issue']} • <span style='color:{priority_color}'>Due in {row['Days']} days</span>
                </div>
                """, unsafe_allow_html=True)
    
    with tab4:
        st.subheader("📸 Photo Intelligence Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_photos = sum(p['total_captures'] for p in st.session_state.projects)
        col1.metric("Total Photos", f"{total_photos:,}")
        col2.metric("Avg per Project", f"{total_photos // len(st.session_state.projects):,}")
        col3.metric("AI Processing Cost", "$127.35")
        col4.metric("Coverage Rate", "94%")
        
        st.markdown("---")
        
        # Photo timeline
        st.markdown("**📅 Photo Capture Timeline**")
        
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        photo_counts = [50 + (i % 20) * 5 for i in range(90)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=photo_counts, mode='lines', fill='tozeroy',
                                line=dict(color='#3b82f6'), name='Daily Captures'))
        fig.update_layout(title="Daily Photo Captures (Last 90 Days)", xaxis_title="Date", 
                         yaxis_title="Photos", height=300)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- COMPLIANCE VIEW ----------------
elif st.session_state.current_view == 'compliance':
    
    st.title("⚖️ NYC DOB Compliance Center")
    
    tab1, tab2, tab3 = st.tabs(["🚨 Active Violations", "📋 Inspection Calendar", "📖 Code Reference"])
    
    with tab1:
        st.subheader("Active DOB Violations Across Portfolio")
        
        # Sample violation data
        violations = [
            {"Project": "Brooklyn Navy Yard", "Type": "Scaffolding", "Code": "BC 3301.9", "Issued": "2024-12-15", "Fine": 5000, "Status": "Open"},
            {"Project": "270 Park Ave", "Type": "Safety Fence", "Code": "BC 3307.6", "Issued": "2024-12-20", "Fine": 2500, "Status": "Pending"},
        ]
        
        if violations:
            st.error(f"🚨 **{len(violations)} Active Violations** requiring immediate attention")
            
            viol_df = pd.DataFrame(violations)
            st.dataframe(viol_df, use_container_width=True, hide_index=True)
            
            total_fines = sum(v['Fine'] for v in violations)
            st.metric("Total Outstanding Fines", f"${total_fines:,}")
        else:
            st.success("✅ No active violations across portfolio")
    
    with tab2:
        st.subheader("Required Inspections & Deadlines")
        
        # Sample inspection schedule
        inspections = [
            {"Project": "Hudson Yards", "Type": "Structural Steel", "Required": "2025-01-15", "Status": "Scheduled"},
            {"Project": "270 Park Ave", "Type": "Fireproofing", "Required": "2025-01-22", "Status": "Pending"},
            {"Project": "Brooklyn Navy", "Type": "Foundation", "Required": "2025-01-08", "Status": "Overdue"}
        ]
        
        insp_df = pd.DataFrame(inspections)
        
        def status_styling(status):
            colors = {"Scheduled": "🟢", "Pending": "🟡", "Overdue": "🔴"}
            return f"{colors.get(status, '⚪')} {status}"
        
        insp_df['Status'] = insp_df['Status'].apply(status_styling)
        st.dataframe(insp_df, use_container_width=True, hide_index=True)
        
        overdue_count = len([i for i in inspections if i['Status'] == 'Overdue'])
        if overdue_count > 0:
            st.warning(f"⚠️ {overdue_count} inspection(s) overdue")
    
    with tab3:
        st.subheader("NYC Building Code Quick Reference")
        
        code_sections = {
            "Chapter 33 - Safeguards During Construction": "Covers temporary structures, safety fencing, and site protection requirements",
            "Chapter 17 - Special Inspections": "Defines required inspections for structural elements and fireproofing",
            "Chapter 28 - Administrative": "Filing procedures, permit requirements, and DOB compliance process"
        }
        
        for section, description in code_sections.items():
            with st.expander(f"📖 {section}"):
                st.write(description)
                st.markdown("[View full code section →](https://codes.iccsafe.org/)")

# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#6b7280; font-size:0.875rem;'>
    <strong>SentinelScope Pro v2.8</strong> • Powered by DeepSeek AI • NYC DOB Real-Time Data<br>
    © 2025 ThriveAI • <a href='#'>Privacy Policy</a> • <a href='#'>Terms of Service</a> • <a href='#'>Support</a>
</div>
""", unsafe_allow_html=True)
