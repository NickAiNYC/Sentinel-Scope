import requests
from typing import List, Dict

def fetch_live_dob_alerts(query_params: Dict) -> List[Dict]:
    """
    Renamed to match app.py imports.
    Queries NYC OpenData for active DOB ECB Violations.
    Dataset: https://data.cityofnewyork.us/resource/6bgk-3dad.json
    """
    bbl = query_params.get("bbl")
    if not bbl:
        return []
    
    # NYC Open Data Socrata Endpoint for DOB ECB Violations
    endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"
    
    # We filter by BBL. We also select specific columns so the UI table stays clean.
    params = {
        "bbl": bbl,
        "$limit": 10,
        "$order": "isn_dob_bis_extract DESC", # Get the most recent first
        "$select": "violation_number, violation_type, issue_date, violation_category, respondent_name"
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Clean up the data: formatting dates for the UI
            for item in data:
                if 'issue_date' in item:
                    item['issue_date'] = item['issue_date'][:10] # Clean "YYYY-MM-DD"
            return data
        return []
    except Exception as e:
        print(f"DOB API Error: {e}")
        return []
