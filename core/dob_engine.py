import requests
import os
from typing import List, Dict

# 1. Standalone function for direct import (Fixes app.py line 16)
def fetch_live_dob_alerts(query_params: Dict) -> List[Dict]:
    """
    Queries NYC OpenData for active DOB ECB Violations using BBL.
    """
    bbl = query_params.get("bbl")
    if not bbl:
        return []

    endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"
    app_token = os.getenv("NYC_DATA_APP_TOKEN")
    
    headers = {"X-App-Token": app_token} if app_token else {}
    params = {
        "bbl": str(bbl),
        "$limit": 10,
        "$order": "issue_date DESC", 
        "$select": "violation_number, violation_type, issue_date, violation_category, respondent_name"
    }

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if 'issue_date' in item:
                    item['issue_date'] = item['issue_date'][:10]
                if 'respondent_name' in item:
                    item['respondent_name'] = str(item['respondent_name']).title()
            return data
        return []
    except Exception as e:
        print(f"DOB API Error: {e}")
        return []

# 2. Class wrapper for structural consistency
class DOBEngine:
    """NYC DOB Data Integration Engine."""
    @staticmethod
    def fetch_live_dob_alerts(query_params: Dict) -> List[Dict]:
        return fetch_live_dob_alerts(query_params)

# 3. Explicit Export
__all__ = ['DOBEngine', 'fetch_live_dob_alerts']
