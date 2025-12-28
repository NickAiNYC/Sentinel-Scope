"""
SentinelScope Constants v2025.12
Hard-coded domain knowledge for NYC Building Code (BC) 2022 + EBC 2025.
Integrated with 2025 Architectural Earth-Tone Design Tokens.
"""

# --- UI DESIGN TOKENS (2025 Architectural Palette) ---
# Updated to include "True Joy" accents and modern biophilic earth tones
BRAND_THEME = {
    "BACKGROUND_BEIGE": "#F5F5DD",  # Bone/Parchment
    "SIDEBAR_TAN": "#D2B48C",       # Raw Sienna
    "PRIMARY_BROWN": "#5C4033",     # Deep Espresso
    "SADDLE_BROWN": "#8B4513",      # Rust Oxide
    "MAHOGANY": "#4E2C23",          # Burnt Umber
    "SUCCESS_GREEN": "#4F7942",     # Sage/Olive (Biophilic)
    "DANGER_RUST": "#8B0000",       # Deep Hematite
    "WARNING_AMBER": "#FFBF00",     # Amber/True Joy (High Visibility)
}

# --- NYC GEOGRAPHY & JURISDICTION ---
BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]

# --- NYC BUILDING CODE 2022 & 2025 UPDATES ---
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
        "ELECTRICAL": "NYC Electrical Code (Effective 12/21/2025)"
    },
    "SITE_SAFETY": "BC Chapter 33",
    "EXISTING_BUILDING": "NYC EBC (Effective 11/07/2025)", 
    "PARAPETS": "1 RCNY 103-15 (Annual Inspection Rule)" 
}

# --- DOB VIOLATION SEVERITY & CLASSES ---
# NYC DOB Class logic: A (Non-Hazardous), B (Hazardous), C (Immediately Hazardous)
DOB_CLASS_MAP = {
    "CRITICAL": "Class C",
    "HIGH": "Class B",
    "MEDIUM": "Class B",
    "LOW": "Class A"
}

DOB_CLASS_DESCRIPTIONS = {
    "Class C": "Immediately Hazardous - Requires 24-hour remediation.",
    "Class B": "Hazardous - Remediation required within 30-45 days.",
    "Class A": "Non-Hazardous - Minor administrative or zoning infraction."
}

# --- CONSTRUCTION MILESTONES (Phase-Specific) ---
MILESTONES = {
    "EXCAVATION": "Foundation & Earthwork",
    "SUPERSTRUCTURE": "Structural Frame / Superstructure",
    "MEP_ROUGH_IN": "MEP Rough-in",
    "ENCLOSURE": "Building Envelope & Glazing",
    "INTERIOR_FINISH": "Drywall & Interior Finishes",
    "TOP_OUT": "Roofing & Mechanical Bulkhead"
}

# --- COMPLIANCE SCORING WEIGHTS (2025 Weights) ---
SCORING_WEIGHTS = {
    "LIFE_SAFETY": 0.40,      # Chapter 33 Site Safety
    "STRUCTURAL": 0.35,       # Foundations/Steel/Concrete
    "ENERGY_EFFICIENCY": 0.15, # LL97 Carbon Compliance
    "ADMINISTRATIVE": 0.10     # Permits/Filing
}

# --- AI AGENT DEFAULTS (Late 2025 Standard) ---
# Using the reasoning-optimized models for forensic auditing
DEFAULT_MODEL = "deepseek-v3.2" 
REASONING_MODEL = "claude-3-5-sonnet" # Optimized for high-token NYC code analysis
DEFAULT_CONFIDENCE_THRESHOLD = 0.85 # Increased threshold for forensic validation
