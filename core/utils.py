"""
SentinelScope Utilities
Helper functions for data validation and coordinate sanitization.
"""

from typing import Tuple, Dict

# NYC Bounding Box (Approximate limits of the 5 boroughs)
NYC_BOUNDS = {
    "min_lat": 40.4774,
    "max_lat": 40.9176,
    "min_lon": -74.2591,
    "max_lon": -73.7002
}

def is_within_nyc(lat: float, lon: float) -> bool:
    """
    Validates if a given coordinate pair falls within NYC limits.
    Prevents off-site data processing and API credit waste.
    """
    return (NYC_BOUNDS["min_lat"] <= lat <= NYC_BOUNDS["max_lat"] and 
            NYC_BOUNDS["min_lon"] <= lon <= NYC_BOUNDS["max_lon"])

def sanitize_text(text: str) -> str:
    """Cleans up AI/OCR noise for professional reporting."""
    if not text:
        return ""
    # Remove excessive whitespace and non-printable characters
    cleaned = " ".join(text.split())
    return cleaned.strip()

def format_risk_label(score: float) -> Dict[str, str]:
    """Returns consistent UI styling based on compliance score."""
    if score >= 90:
        return {"label": "LOW", "color": "green", "icon": "✅"}
    if score >= 70:
        return {"label": "MEDIUM", "color": "orange", "icon": "⚠️"}
    return {"label": "HIGH", "color": "red", "icon": "🚨"}
