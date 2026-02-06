"""
Veteran Dashboard - NYC Project Opportunity Matching
Filters opportunities by Level and Compliance Readiness.
"""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# Add root to path for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core.constants import BRAND_THEME
from packages.agents.opportunity import (
    AgencyType,
    FeasibilityScorer,
    OpportunityClassifier,
    OpportunityLevel,
    UserComplianceProfile,
)
from tests.simulator import OpportunitySimulator


# ====== UI CONFIG & THEME ======
st.set_page_config(
    page_title="Veteran Dashboard | Opportunity Matching",
    page_icon="🎖️",
    layout="wide"
)

bg_color = BRAND_THEME.get('BACKGROUND_BEIGE', '#F5F5DC')
primary_color = BRAND_THEME.get('PRIMARY_BROWN', '#5D4037')

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    h1, h2, h3 {{ color: {primary_color}; font-weight: 800; }}
    .opportunity-card {{
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #ddd;
        margin-bottom: 15px;
        background-color: white;
    }}
    .status-badge {{
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 12px;
    }}
    .contestable {{ background-color: #4CAF50; color: white; }}
    .soft-open {{ background-color: #FF9800; color: white; }}
    .closed {{ background-color: #9E9E9E; color: white; }}
    .compliant {{ color: #4CAF50; font-size: 24px; }}
    .not-compliant {{ color: #F44336; font-size: 24px; }}
    </style>
""", unsafe_allow_html=True)


# ====== SESSION STATE INITIALIZATION ======
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = None
if 'user_profile' not in st.session_state:
    # Default user profile for demo
    st.session_state.user_profile = UserComplianceProfile(
        user_id="DEMO-USER",
        company_name="Demo Construction LLC",
        general_liability_limit=5_000_000,
        workers_comp_limit=5_000_000,
        umbrella_limit=10_000_000,
        insurance_expiry=datetime.now() + timedelta(days=365),
        active_licenses=["General Contractor", "Electrical"],
        license_expiry={
            "General Contractor": datetime.now() + timedelta(days=365),
            "Electrical": datetime.now() + timedelta(days=365),
        },
        has_active_dob_registration=True
    )


# ====== HEADER ======
st.title("🎖️ Veteran Dashboard - NYC Project Opportunities")
st.markdown("**Conservative Opportunity Matching with Compliance Cross-Reference**")
st.markdown("---")


# ====== SIDEBAR - USER PROFILE ======
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/skyscraper.png", width=70)
    st.title("Your Compliance Profile")
    st.markdown("---")
    
    profile = st.session_state.user_profile
    
    st.subheader(profile.company_name)
    st.write(f"**User ID:** {profile.user_id}")
    
    st.markdown("### Insurance Coverage")
    st.write(f"• General Liability: ${profile.general_liability_limit:,}")
    st.write(f"• Workers Comp: ${profile.workers_comp_limit:,}")
    if profile.umbrella_limit:
        st.write(f"• Umbrella: ${profile.umbrella_limit:,}")
    st.write(f"• Expires: {profile.insurance_expiry.date()}")
    
    st.markdown("### Active Licenses")
    for license in profile.active_licenses:
        expiry = profile.license_expiry.get(license, datetime.now())
        st.write(f"✅ {license} (exp: {expiry.date()})")
    
    st.markdown("### DOB Registration")
    if profile.has_active_dob_registration:
        st.success("✅ Active")
    else:
        st.error("❌ Inactive")
    
    st.markdown("---")
    
    # Simulation controls
    st.subheader("Load Opportunities")
    
    with st.form("load_opportunities"):
        num_samples = st.slider("Number of Samples", 5, 50, 20)
        use_demo_mode = st.checkbox("Demo Mode (Skip API)", value=True, 
                                    help="Use simulator only, no real API calls")
        load_btn = st.form_submit_button("🔄 Load NYC Opportunities")


# ====== LOAD OPPORTUNITIES ======
if load_btn:
    with st.spinner("Loading NYC project opportunities..."):
        # Generate sample opportunities using simulator
        simulator = OpportunitySimulator()
        samples = simulator.generate_batch(
            count=num_samples,
            distribution={
                "closed": 0.5,
                "soft_open": 0.3,
                "contestable": 0.2
            }
        )
        
        opportunities = []
        scorer = FeasibilityScorer()
        
        # If not in demo mode and API key is available, classify with AI
        if not use_demo_mode and os.getenv("ANTHROPIC_API_KEY"):
            classifier = OpportunityClassifier(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            for sample in samples:
                # Real AI classification
                opp = classifier.classify(
                    project_id=sample['project_id'],
                    project_title=sample['title'],
                    agency_text=sample['agency_text'],
                    agency=sample['agency'],
                    estimated_value=sample.get('estimated_value'),
                    trade_category=sample.get('trade_category')
                )
                
                # Run feasibility check
                feasibility = scorer.check_feasibility(opp, profile)
                
                opportunities.append({
                    'classification': opp,
                    'feasibility': feasibility
                })
        else:
            # Demo mode: Use expected classification from simulator
            from packages.agents.opportunity.models import (
                DecisionProof,
                OpportunityClassification,
            )
            
            for sample in samples:
                # Create opportunity from simulator expectation
                opp_level = OpportunityLevel[sample['expected_classification']]
                
                opp = OpportunityClassification(
                    project_id=sample['project_id'],
                    project_title=sample['title'],
                    agency=sample['agency'],
                    opportunity_level=opp_level,
                    decision_proof=DecisionProof(
                        decision=opp_level,
                        confidence=0.85,
                        reasoning=f"Demo mode classification: {opp_level.value}",
                        text_signals=[],
                        red_flags=[]
                    ),
                    raw_text=sample['agency_text'],
                    estimated_value=sample.get('estimated_value'),
                    trade_category=sample.get('trade_category')
                )
                
                # Run feasibility check
                feasibility = scorer.check_feasibility(opp, profile)
                
                opportunities.append({
                    'classification': opp,
                    'feasibility': feasibility
                })
        
        st.session_state.opportunities = opportunities
        st.success(f"✅ Loaded {len(opportunities)} opportunities")


# ====== FILTERS ======
if st.session_state.opportunities:
    opportunities = st.session_state.opportunities
    
    st.subheader("🔍 Filter Opportunities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        level_filter = st.multiselect(
            "Opportunity Level",
            options=["CLOSED", "SOFT_OPEN", "CONTESTABLE"],
            default=["CONTESTABLE", "SOFT_OPEN"]
        )
    
    with col2:
        compliance_filter = st.selectbox(
            "Compliance Readiness",
            options=["All", "Compliant Only", "Non-Compliant Only"]
        )
    
    with col3:
        agency_filter = st.multiselect(
            "Agency",
            options=[a.value for a in AgencyType],
            default=[a.value for a in AgencyType]
        )
    
    st.markdown("---")
    
    # Apply filters
    filtered_opps = opportunities
    
    if level_filter:
        filtered_opps = [
            o for o in filtered_opps 
            if o['classification'].opportunity_level.value in level_filter
        ]
    
    if compliance_filter == "Compliant Only":
        filtered_opps = [o for o in filtered_opps if o['feasibility'].is_compliant]
    elif compliance_filter == "Non-Compliant Only":
        filtered_opps = [o for o in filtered_opps if not o['feasibility'].is_compliant]
    
    if agency_filter:
        filtered_opps = [
            o for o in filtered_opps 
            if o['classification'].agency.value in agency_filter
        ]
    
    # ====== SUMMARY METRICS ======
    st.subheader("📊 Summary")
    
    total_opps = len(filtered_opps)
    contestable_count = sum(
        1 for o in filtered_opps 
        if o['classification'].opportunity_level == OpportunityLevel.CONTESTABLE
    )
    compliant_count = sum(1 for o in filtered_opps if o['feasibility'].is_compliant)
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Total Opportunities", total_opps)
    metric_col2.metric("Contestable", contestable_count)
    metric_col3.metric("Ready to Bid", compliant_count)
    metric_col4.metric("Match Rate", f"{(compliant_count/total_opps*100) if total_opps > 0 else 0:.0f}%")
    
    st.markdown("---")
    
    # ====== OPPORTUNITY CARDS ======
    st.subheader(f"💼 Opportunities ({len(filtered_opps)})")
    
    if not filtered_opps:
        st.info("No opportunities match your filters. Try adjusting the criteria.")
    else:
        for opp_data in filtered_opps:
            opp = opp_data['classification']
            feasibility = opp_data['feasibility']
            
            # Determine badge styling
            level_class = opp.opportunity_level.value.lower().replace("_", "-")
            compliance_icon = "✅" if feasibility.is_compliant else "❌"
            compliance_class = "compliant" if feasibility.is_compliant else "not-compliant"
            
            with st.container():
                # Header row
                col_title, col_status, col_compliance = st.columns([3, 1, 1])
                
                with col_title:
                    st.markdown(f"### {opp.project_title}")
                    st.caption(f"**Project ID:** {opp.project_id} | **Agency:** {opp.agency.value}")
                
                with col_status:
                    st.markdown(
                        f'<span class="status-badge {level_class}">{opp.opportunity_level.value}</span>',
                        unsafe_allow_html=True
                    )
                
                with col_compliance:
                    st.markdown(
                        f'<div class="{compliance_class}">{compliance_icon} {"Ready" if feasibility.is_compliant else "Not Ready"}</div>',
                        unsafe_allow_html=True
                    )
                
                # Details in expander
                with st.expander("📋 View Details"):
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.markdown("**Project Information**")
                        if opp.estimated_value:
                            st.write(f"• Estimated Value: ${opp.estimated_value:,}")
                        if opp.trade_category:
                            st.write(f"• Trade: {opp.trade_category}")
                        
                        st.markdown("**Classification Analysis**")
                        st.write(f"• Confidence: {opp.decision_proof.confidence:.0%}")
                        st.write(f"• Reasoning: {opp.decision_proof.reasoning}")
                        
                        if opp.decision_proof.text_signals:
                            st.write("• Key Signals:")
                            for signal in opp.decision_proof.text_signals[:3]:
                                st.write(f"  - {signal}")
                        
                        if opp.decision_proof.red_flags:
                            st.warning("⚠️ Red Flags:")
                            for flag in opp.decision_proof.red_flags:
                                st.write(f"  - {flag}")
                    
                    with detail_col2:
                        st.markdown("**Feasibility Assessment**")
                        st.write(f"• Feasibility Score: {feasibility.feasibility_score:.0f}/100")
                        
                        # Insurance status
                        if feasibility.insurance_compliant:
                            st.success("✅ Insurance: Compliant")
                        else:
                            st.error("❌ Insurance: Gaps Found")
                            for gap in feasibility.insurance_gaps:
                                st.write(f"  - {gap}")
                        
                        # License status
                        if feasibility.license_compliant:
                            st.success("✅ Licenses: Compliant")
                        else:
                            st.error("❌ Licenses: Gaps Found")
                            for gap in feasibility.license_gaps:
                                st.write(f"  - {gap}")
                        
                        # Other barriers
                        if feasibility.other_barriers:
                            st.warning("⚠️ Other Barriers:")
                            for barrier in feasibility.other_barriers:
                                st.write(f"  - {barrier}")
                        
                        # Next steps
                        if feasibility.next_steps:
                            st.markdown("**Next Steps:**")
                            for step in feasibility.next_steps:
                                st.write(f"• {step}")
                    
                    # Show raw agency text
                    with st.expander("📄 Raw Agency Text"):
                        st.text(opp.raw_text)
                
                st.markdown("---")

else:
    # Initial state - show instructions
    st.info("""
    👋 **Welcome to the Veteran Dashboard!**
    
    This tool helps you find NYC project opportunities that match your compliance profile.
    
    **Features:**
    - 🎯 **Conservative Classification:** Uses skeptical AI analysis to avoid false positives
    - ✅ **Compliance Cross-Reference:** Automatically checks if you meet insurance and license requirements
    - 🔍 **Smart Filtering:** Filter by opportunity level and compliance readiness
    - 📊 **Detailed Analysis:** See exactly why each project is or isn't a good match
    
    **Get Started:**
    1. Review your compliance profile in the sidebar (using demo data)
    2. Click "Load NYC Opportunities" to see available projects
    3. Use filters to find opportunities you're ready to bid on
    
    **Opportunity Levels:**
    - 🟢 **CONTESTABLE:** Confirmed open for bidding - you can submit now
    - 🟠 **SOFT_OPEN:** May be open but unclear - proceed with caution
    - ⚪ **CLOSED:** Not open for bidding - planning phase only
    """)
    
    st.markdown("---")
    st.subheader("Sample Opportunities")
    st.write("Load opportunities using the sidebar to see NYC projects matched to your profile.")
