import requests
from typing import List, Dict, Optional
import os

class DOBEngine:
    """
    NYC DOB Data Integration Engine.
    Connects to NYC Open Data (Socrata) to pull real-time building violations.
    """

    @staticmethod
    def fetch_live_dob_alerts(query_params: Dict) -> List[Dict]:
        """
        Queries NYC OpenData for active DOB ECB Violations using BBL.
        Dataset: DOB ECB Violations (https://data.cityofnewyork.us/resource/6bgk-3dad.json)
        """
        bbl = query_params.get("bbl")
        if not bbl:
            return []

        # NYC Open Data Socrata Endpoint
        endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"
        
        # Pull App Token from environment for higher rate limits
        app_token = os.getenv("NYC_DATA_APP_TOKEN")
        
        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token

        # Filter by BBL and order by most recent
        params = {
            "bbl": bbl,
            "$limit": 10,
            "$order": "issue_date DESC", 
            "$select": "violation_number, violation_type, issue_date, violation_category, respondent_name"
        }

        try:
            response = requests.get(
                endpoint, 
                params=params, 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format dates and clean strings for the Streamlit UI
                for item in data:
                    if 'issue_date' in item:
                        item['issue_date'] = item['issue_date'][:10]
                    
                    # Clean up respondent names (often in ALL CAPS)
                    if 'respondent_name' in item:
                        item['respondent_name'] = item['respondent_name'].title()
                        
                return data
            
            print(f"NYC Data Portal returned status: {response.status_code}")
            return []

        except Exception as e:
            print(f"Critical DOB API Error: {e}")
            return []
