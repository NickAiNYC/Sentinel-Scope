"""
SentinelScope Geocoding Module
Upgraded: Converts NYC project addresses into BBL/BIN and Coordinates.
"""
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from typing import Optional, Dict

class ProjectLocator:
    def __init__(self, user_agent: str = "sentinel_scope_compliance_agent"):
        self.geolocator = Nominatim(user_agent=user_agent)
        # NYC Geoclient API (Requires account at developer.cityofnewyork.us)
        self.geoclient_key = st.secrets.get("NYC_GEOCLIENT_KEY", None)

    def lookup_nyc_property(self, address: str) -> Dict:
        """
        Primary NYC-specific lookup. Fetches BBL and BIN.
        """
        # For demo purposes, we provide a mock BBL for common NYC addresses 
        # unless the API key is set in Streamlit Secrets.
        if not self.geoclient_key:
            return {
                "lat": 40.7554, "lon": -73.9755, 
                "bbl": "1012650001", "bin": "1034440",
                "status": "success", "note": "Mock Data (No API Key)"
            }

        try:
            # High-tech: Query NYC's official geocoder
            url = f"https://api.nyc.gov/geo/geoclient/v1/search.json"
            params = {"input": address, "subscription-key": self.geoclient_key}
            response = requests.get(url, params=params, timeout=5).json()
            
            results = response.get('results', [{}])[0].get('response', {})
            if results:
                return {
                    "lat": float(results.get('latitudeInternalLabel')),
                    "lon": float(results.get('longitudeInternalLabel')),
                    "bbl": results.get('bbl'),
                    "bin": results.get('buildingIdentificationNumber'),
                    "status": "success"
                }
        except Exception:
            pass
        return {"status": "error"}

    def get_coordinates_fallback(self, address: str) -> Optional[Dict]:
        """Original Nominatim logic as a safety fallback."""
        try:
            search_query = f"{address}, New York, NY"
            location = self.geolocator.geocode(search_query)
            if location:
                return {"lat": location.latitude, "lon": location.longitude, "status": "success"}
        except GeopyError:
            return None
        return None

def lookup_address(address: str):
    locator = ProjectLocator()
    # Try the high-tech property lookup first
    result = locator.lookup_nyc_property(address)
    
    if result["status"] == "success":
        return result
        
    # Fallback to standard coordinates
    fallback = locator.get_coordinates_fallback(address)
    if fallback:
        return fallback
        
    return {"status": "error", "message": "Address not found"}
