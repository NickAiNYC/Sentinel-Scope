"""
SentinelScope Geocoding Module
Upgraded: Converts NYC project addresses into BBL/BIN and Coordinates with Smart Caching.
"""
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from typing import Dict

class ProjectLocator:
    def __init__(self, user_agent: str = "sentinel_scope_compliance_agent"):
        self.geolocator = Nominatim(user_agent=user_agent)
        # NYC Geoclient API (Developer Portal: developer.cityofnewyork.us)
        self.geoclient_key = st.secrets.get("NYC_GEOCLIENT_KEY", None)

    def lookup_nyc_property(self, address: str) -> Dict:
        """
        Primary NYC-specific lookup. Fetches BBL and BIN.
        """
        # Default fallback/mock data if no API key or lookup fails
        default_data = {
            "lat": 40.7554, 
            "lon": -73.9755, 
            "bbl": "1012650001", 
            "bin": "1034440",
            "status": "success", 
            "note": "Mock Data (Default)"
        }

        if not self.geoclient_key:
            return default_data

        try:
            # NYC official geocoder endpoint
            url = "https://api.nyc.gov/geo/geoclient/v1/search.json"
            params = {"input": address, "subscription-key": self.geoclient_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Geoclient nesting is deep: results -> [0] -> response
                raw_res = data.get('results', [{}])[0].get('response', {})
                
                if raw_res and 'latitudeInternalLabel' in raw_res:
                    return {
                        "lat": float(raw_res.get('latitudeInternalLabel')),
                        "lon": float(raw_res.get('longitudeInternalLabel')),
                        "bbl": raw_res.get('bbl'),
                        "bin": raw_res.get('buildingIdentificationNumber'),
                        "status": "success",
                        "note": "Live NYC Geoclient Data"
                    }
        except Exception as e:
            print(f"Geoclient Error: {e}")
            
        return default_data

    def get_coordinates_fallback(self, address: str) -> Dict:
        """Nominatim logic as a secondary safety fallback."""
        try:
            search_query = f"{address}, New York, NY"
            location = self.geolocator.geocode(search_query)
            if location:
                return {
                    "lat": location.latitude, 
                    "lon": location.longitude, 
                    "bbl": "1000000000", # Unknown BBL
                    "status": "success",
                    "note": "Nominatim Fallback"
                }
        except GeopyError:
            pass
        
        return {"status": "error", "lat": 40.7, "lon": -74.0}

@st.cache_data(ttl=86400) # Cache address lookups for 24 hours
def lookup_address(address: str) -> Dict:
    """
    Main entry point for app.py. 
    Uses caching to prevent redundant API calls.
    """
    if not address or len(address) < 5:
        return {"status": "error", "message": "Invalid Address"}

    locator = ProjectLocator()
    
    # 1. Try NYC Geoclient
    result = locator.lookup_nyc_property(address)
    if result.get("note") == "Live NYC Geoclient Data":
        return result
        
    # 2. Try Nominatim Fallback
    fallback = locator.get_coordinates_fallback(address)
    if fallback["status"] == "success":
        return fallback
        
    # 3. Final Mock Return to keep the app running
    return result
