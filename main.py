# main.py
import time

import streamlit as st

from core.auth import sign_in, sign_out, sign_up
from core.database import (
    create_project,
    get_db_client,
    get_projects_for_user,
    save_audit,
)
from core.gap_detector import ComplianceGapEngine
from core.processor import SentinelBatchProcessor
from core.report_generator import SentinelReportGenerator


# ========================================================================
# AUTHENTICATION PAGE
# ========================================================================
def login_page():
    st.title("SentinelScope SaaS")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # Login Tab
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Enter Dashboard", type="primary"):
            success, msg = sign_in(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.current_view = "dashboard"
                st.rerun()
            else:
                st.error(f"Login Failed: {msg}")

    # Sign Up Tab
    with tab2:
        new_email = st.text_input("Email")
        full_name = st.text_input("Full Name")
        if st.button("Create Account"):
            success, msg = sign_up(new_email, full_name)
            if success:
                st.success(f"Account Created: {msg}")
                st.session_state.logged_in = True
                st.session_state.current_view = "dashboard"
                st.rerun()
            else:
                st.error(f"Sign Up Failed: {msg}")


# ========================================================================
# DASHBOARD PAGE
# ========================================================================
def dashboard_page():
    # Check Login
    if "user" not in st.session_state:
        st.session_state.current_view = "login"
        st.rerun()

    user = st.session_state.user
    st.write(f"Welcome back, {user['full_name']}")

    # Navigation
    col_new, col_dash = st.columns([1, 4])
    with col_new:
        if st.button("➕ New Project"):
            st.session_state.sub_view = "new_project"

    # 1. New Project View
    if st.session_state.get("sub_view") == "new_project":
        with st.form("new_project_form"):
            name = st.text_input("Project Name")
            address = st.text_input("Address")
            p_type = st.selectbox(
                "Type", ["Commercial High-Rise", "Residential", "Industrial"]
            )
            value = st.number_input("Value ($)", 0)

            if st.form_submit_button("Create Project"):
                new_id = create_project(
                    {
                        "name": name,
                        "address": address,
                        "project_type": p_type,
                        "project_value": value,
                        "status": "active",
                    }
                )
                st.success("Project Created!")
                st.session_state.sub_view = None
                st.rerun()

    # 2. Project List
    projects = get_projects_for_user(user["id"])

    st.subheader("My Projects")
    if not projects:
        st.info("No projects yet.")
    else:
        for p in projects:
            with st.expander(f"🏗️ {p['name']}"):
                st.metric("Compliance", f"{p.get('compliance_score', 0)}%")
                st.metric("Risk", f"{p.get('risk_score', 0)}/100")


# ========================================================================
# AUDIT PAGE (Your old logic, but restricted)
# ========================================================================
def audit_page(project_id: str):
    user = st.session_state.user
    # Verify ownership (Security)
    projects = get_projects_for_user(user["id"])
    project = next((p for p in projects if p["id"] == project_id), None)

    if not project:
        st.error("Access Denied")
        return

    st.write(f"Auditing: {project['name']}")

    uploaded_files = st.file_uploader(
        "Upload Photos", type=["png", "jpg"], accept_multiple_files=True
    )

    if uploaded_files and st.button("Run AI Audit", type="primary"):
        gap_engine = ComplianceGapEngine(project_type=project["project_type"])
        processor = SentinelBatchProcessor(
            engine=gap_engine,
            api_key=st.secrets["DEEPSEEK_API_KEY"],
            max_workers=6,
        )

        results = processor.run_audit(
            file_sources=uploaded_files,
            project_type=project["project_type"],
            enable_cache=True,
        )

        milestones = [r["milestone"] for r in results if r.get("milestone")]
        gap_analysis = gap_engine.detect_gaps(milestones)

        st.json(gap_analysis.model_dump())

        # Save to DB
        save_audit(project_id, gap_analysis.model_dump())
        st.success("Audit Saved to Database")


# ========================================================================
# ROUTER
# ========================================================================
def main():
    # Init Session
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_view" not in st.session_state:
        st.session_state.current_view = "login"

    # Routing
    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.current_view == "dashboard":
        dashboard_page()
    elif "audit_target" in st.query_params:
        audit_page(st.query_params["audit_target"])
    else:
        dashboard_page()  # Default


if __name__ == "__main__":
    main()
