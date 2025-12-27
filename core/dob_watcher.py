import requests
import pandas as pd
from datetime import datetime, timedelta

def get_active_permits(bbl: str):
    """
    Fetch active permits for a specific BBL from NYC Open Data.
    Example BBL: '3070620001' (Borough 3, Block 7062, Lot 1)
    """
    # Dataset ID for DOB NOW: Build Approved Permits
    DATASET_ID = "w9ak-ipjd" 
    API_URL = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
    
    # Query: Filter by BBL and only show active/issued permits
    # We use SoQL (Socrata Query Language)
    params = {
        "$where": f"bin = '{bbl}'", # Or use 'bin' or 'job_number'
        "$limit": 50
    }
    
    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        return None
        
    data = response.json()
    if not data:
        return "No active permits found."

    df = pd.DataFrame(data)
    
    # Logic: Check for expiring permits
    today = datetime.now()
    df['expiration_date'] = pd.to_datetime(df['expiration_date'])
    
    # Flag permits expiring in the next 14 days
    df['alert_level'] = df['expiration_date'].apply(
        lambda x: "🚨 CRITICAL" if (x - today).days < 7 
        else ("⚠️ WARNING" if (x - today).days < 14 else "✅ OK")
    )
    
    return df[['permit_number', 'work_type', 'expiration_date', 'alert_level']]

# Example usage for Tilyou Towers area
# print(get_active_permits("3070620001"))
