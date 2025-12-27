"""
SentinelScope Constants
Hard-coded domain knowledge for NYC Building Code (BC) 2022.
"""

# --- NYC GEOGRAPHY ---
BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]

# --- NYC BUILDING CODE 2022 REFERENCES ---
# These are the actual chapters your Gap Detector will cite in reports.
NYC_BC_REFS = {
    "STRUCTURAL": {
        "CHAPTER": "BC Chapter 16",
        "STEEL": "BC Chapter 22",
        "CONCRETE": "BC Chapter 19",
        "FOUNDATIONS": "BC Chapter 18"
    },
    "FIRE_PROTECTION": {
        "FIRE_RESISTANCE": "BC Chapter 7",
        "PROTECTION_SYSTEMS": "BC Chapter 9",
        "FIREBLOCKING": "BC Section 718"
    },
    "MEP": {
        "MECHANICAL": "NYC Mechanical Code Chapter 6",
        "PLUMBING": "NYC Plumbing Code Chapter 7",
        "FUEL_GAS": "NYC Fuel Gas Code Chapter 4"
    },
    "SITE_SAFETY": "BC Chapter 33"
}

# --- CONSTRUCTION MILESTONES ---
# Used by the Classifier to normalize AI detections.
MILESTONES = {
    "EXCAVATION": "Foundation & Earthwork",
    "SUPERSTRUCTURE": "Structural Frame / Superstructure",
    "MEP_ROUGH_IN": "MEP Rough-in",
    "ENCLOSURE": "Building Envelope & Glazing",
    "INTERIOR_FINISH": "Drywall & Interior Finishes",
    "TOP_OUT": "Roofing & Mechanical Bulkhead"
}

# --- DOB VIOLATION SEVERITY ---
# Maps Socrata API "Violation Category" to risk levels.
VIOLATION_LEVELS = {
    "VWH": "CRITICAL",  # Violation - Work Without Permit Hazardous
    "VH":  "HIGH",      # Violation Hazardous
    "VW":  "MEDIUM",    # Violation - Work Without Permit
    "ZV":  "LOW"        # Zoning Violation
}

# --- COMPLIANCE SCORING ---
# Weights for the Gap Analysis Engine.
SCORING_WEIGHTS = {
    "LIFE_SAFETY": 0.40,
    "STRUCTURAL": 0.35,
    "ENVIRONMENTAL": 0.15,
    "ADMINISTRATIVE": 0.10
}

# --- UI DESIGN TOKENS ---
# Ensure the Dashboard and PDF look identical.
BRAND_THEME = {
    "PRIMARY_BLUE": "#1E3A8A", # NYC Official Blue
    "CRITICAL_RED": "#DC2626",
    "WARNING_AMBER": "#F59E0B",
    "SUCCESS_GREEN": "#10B981"
}

# --- AI AGENT DEFAULTS ---
DEFAULT_MODEL = "deepseek-v3-vision"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
