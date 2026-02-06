from typing import Any

import requests


def lookup_address(address: str) -> dict[str, Any]:
    """
    Converts a NYC address into Geolocation (Lat/Lon) and BBL.
    Uses NYC Planning Labs GeoSearch API (Free & No Key Required).
    """
    # Default fallback (270 Park Ave)
    default_data = {
        "lat": 40.7559,
        "lon": -73.9754,
        "bbl": "1012650001",
        "formatted_address": "270 Park Ave, New York, NY",
    }

    if not address or "New York" not in address:
        return default_data

    try:
        # NYC Planning GeoSearch API
        url = f"https://geosearch.planninglabs.nyc/v2/search?text={address}&size=1"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("features"):
            feature = data["features"][0]
            props = feature.get("properties", {})
            geom = feature.get("geometry", {}).get("coordinates", [0, 0])

            return {
                "lat": geom[1],
                "lon": geom[0],
                "bbl": props.get("pad_bbl", "1012650001"),
                "formatted_address": props.get("label", address),
            }
    except Exception as e:
        print(f"Geocoding Error: {e}")

    return default_data
