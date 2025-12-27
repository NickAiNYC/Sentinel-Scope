"""
SentinelScope Constants
Hard-coded domain knowledge for NYC Building Code (BC) 2022.
Integrated with Architectural Earth-Tone Design Tokens.
"""

# --- UI DESIGN TOKENS (Architectural Earth-Tone Palette) ---
BRAND_THEME = {
    "BACKGROUND_BEIGE": "#F5F5DD",  # Main app background
    "SIDEBAR_TAN": "#D2B48C",       # Sidebar and secondary panels
    "PRIMARY_BROWN": "#5C4033",     # Deep coffee (Main headers/buttons)
    "SADDLE_BROWN": "#8B4513",      # Accents and icons
    "MAHOGANY": "#4E2C23",          # Progress bars and gauges
    "SUCCESS_GREEN": "#4F7942",     # Sage green for compliance
    "DANGER_RUST": "#8B0000",       # Dark rust for violations
    "WARNING_AMBER": "#B8860B",     # Dark goldenrod for warnings
}

# --- NYC GEOGRAPHY ---
BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]

# --- NYC BUILDING CODE 2022 REFERENCES ---
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
MILESTONES = {
    "EXCAVATION": "Foundation & Earthwork",
    "SUPERSTRUCTURE": "Structural Frame / Superstructure",
    "MEP_ROUGH_IN": "MEP Rough-in",
    "ENCLOSURE": "Building Envelope & Glazing",
    "INTERIOR_FINISH": "Drywall & Interior Finishes",
    "TOP_OUT": "Roofing & Mechanical Bulkhead"
}

# --- DOB VIOLATION SEVERITY ---
VIOLATION_LEVELS = {
    "VWH": "CRITICAL",  # Violation - Work Without Permit Hazardous
    "VH":  "HIGH",      # Violation Hazardous
    "VW":  "MEDIUM",    # Violation - Work Without Permit
    "ZV":  "LOW"        # Zoning Violation
}

# --- COMPLIANCE SCORING ---
SCORING_WEIGHTS = {
    "LIFE_SAFETY": 0.40,
    "STRUCTURAL": 0.35,
    "ENVIRONMENTAL": 0.15,
    "ADMINISTRATIVE": 0.10
}

# --- AI AGENT DEFAULTS ---
DEFAULT_MODEL = "deepseek-v3-vision"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
