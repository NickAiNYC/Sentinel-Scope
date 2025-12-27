import requests
from typing import List, Dict

def fetch_dob_violations(bbl: str) -> List[Dict]:
    """
    Queries NYC OpenData for active DOB ECB Violations.
    Dataset: https://data.cityofnewyork.us/resource/6bgk-3dad.json
    """
    if not bbl: return []
    
    endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"
    # Filter by BBL and prioritize open/recent violations
    params = {
        "bbl": bbl,
        "$order": "isn_dob_bis_extract DESC",
        "$limit": 5
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []
