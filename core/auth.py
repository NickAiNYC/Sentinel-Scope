# core/auth.py
import streamlit as st
from supabase import create_client, Client
import time

# Initialize Supabase
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def sign_in(email: str, password: str):
    """Authenticate user."""
    try:
        # Note: In a real SaaS, you'd check a password hash.
        # For MVP, we just verify email existence.
        response = supabase.table("app_users").select("*").eq("email", email).execute()
        if response.data:
            st.session_state.user = response.data[0]
            return True, "Login Successful"
        return False, "User not found"
    except Exception as e:
        return False, str(e)

def sign_up(email: str, full_name: str):
    """Register new user."""
    try:
        # Check if exists
        existing = supabase.table("app_users").select("*").eq("email", email).execute()
        if existing.data:
            return False, "Email already registered"

        # Create User
        response = supabase.table("app_users").insert({
            "email": email,
            "full_name": full_name,
            "role": "admin", # Default to admin for MVP
            "email_confirmed_at": "time"("utc", now()) # Auto-confirm for MVP
        }).execute()

        if response.data:
            st.session_state.user = response.data[0]
            return True, "Account Created"
        return False, "Failed to create account"
    except Exception as e:
        return False, str(e)

def sign_out():
    """Clear session."""
    if "user" in st.session_state:
        del st.session_state.user
    st.rerun()
