"""
SentinelScope Geocoding Module
Converts NYC project addresses into coordinates for DOB API lookups.
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
from typing import Optional, Tuple, Dict

class ProjectLocator:
    def __init__(self, user_agent: str = "sentinel_scope_compliance_agent"):
        self.geolocator = Nominatim(user_agent=user_agent)

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Converts a physical address string to (Latitude, Longitude).
        Appends ', New York, NY' to ensure local accuracy.
        """
        try:
            # Ensure the search is scoped to NYC
            search_query = f"{address}, New York, NY"
            location = self.geolocator.geocode(search_query)
            
            if location:
                return (location.latitude, location.longitude)
            return None
        except GeopyError as e:
            print(f"Geocoding Error: {e}")
            return None

def lookup_address(address: str):
    locator = ProjectLocator()
    coords = locator.get_coordinates(address)
    if coords:
        return {"lat": coords[0], "lon": coords[1], "status": "success"}
    return {"status": "error", "message": "Address not found"}
