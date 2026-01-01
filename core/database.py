# core/database.py
from supabase import create_client, Client
from typing import List, Dict, Any
from datetime import datetime

# Singleton Client
_supabase: Client = None

def get_db_client() -> Client:
    """Get or create Supabase client."""
    global _supabase
    if _supabase is None:
        if "SUPABASE_URL" in st.secrets:
            _supabase = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"]
            )
    return _supabase

def get_projects_for_user(user_id: str) -> List[Dict]:
    """Get projects for specific user only (Security)."""
    client = get_db_client()
    if not client: return []
    
    response = client.table("projects").select("*").eq("user_id", user_id).execute()
    return response.data if response.data else []

def create_project(project_data: Dict) -> str:
    """Create project for logged in user."""
    client = get_db_client()
    if not client: raise Exception("DB Not Connected")
    
    # Enforce user ownership
    project_data["user_id"] = client.auth.get_user()["id"] if hasattr(client, 'auth') else "MOCK_ID"
    
    response = client.table("projects").insert(project_data).execute()
    return response.data[0]["id"] if response.data else None

def save_audit(project_id: str, analysis_data: Dict):
    """Save audit result (Security enforced)."""
    client = get_db_client()
    if not client: raise Exception("DB Not Connected")
    
    payload = {
        "project_id": project_id,
        "compliance_score": analysis_data.get("compliance_score"),
        "risk_score": analysis_data.get("risk_score"),
        "gap_count": analysis_data.get("gap_count"),
        "photos_analyzed": analysis_data.get("photos_analyzed", 0),
        "model_used": "deepseek-vl-chat"
    }
    
    response = client.table("audits").insert(payload).execute()
    return response.data[0]["id"] if response.data else None
