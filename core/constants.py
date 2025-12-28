"""
SentinelScope Constants v2025.12
Hard-coded domain knowledge for NYC Building Code (BC) 2022 + EBC 2025.
Integrated with 2025 Architectural Earth-Tone Design Tokens.
"""

# --- UI DESIGN TOKENS (2025 Architectural Palette) ---
# Updated to include "True Joy" accents and modern earth tones
BRAND_THEME = {
    "BACKGROUND_BEIGE": "#F5F5DD",  # Bone/Parchment
    "SIDEBAR_TAN": "#D2B48C",       # Raw Sienna
    "PRIMARY_BROWN": "#5C4033",      # Deep Espresso
    "SADDLE_BROWN": "#8B4513",       # Rust Oxide
    "MAHOGANY": "#4E2C23",           # Burnt Umber
    "SUCCESS_GREEN": "#4F7942",      # Sage/Olive (Biophilic)
    "DANGER_RUST": "#8B0000",        # Deep Hematite
    "WARNING_AMBER": "#FFBF00",      # Amber/True Joy (High Visibility)
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
    "EXISTING_BUILDING": "NYC EBC (Effective 11/07/2025)", # New 2025 Code
    "PARAPETS": "1 RCNY 103-15 (Annual Inspection Rule)" # New 2024/25 Rule
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

# --- DOB VIOLATION SEVERITY (Reflecting 2025 Enforcement) ---
VIOLATION_LEVELS = {
    "VWH": "CRITICAL",  # Work Without Permit Hazardous
    "VH":  "HIGH",      # Violation Hazardous
    "VW":  "MEDIUM",    # Work Without Permit
    "ZV":  "LOW",       # Zoning Violation
    "AEU": "HIGH"       # Failed Annual Inspection (New for 2025)
}

# --- COMPLIANCE SCORING WEIGHTS ---
SCORING_WEIGHTS = {
    "LIFE_SAFETY": 0.40,      # Chapter 33 Site Safety
    "STRUCTURAL": 0.35,       # Foundations/Steel/Concrete
    "ENERGY_EFFICIENCY": 0.15, # Local Law 97/33 (2025 Penalties)
    "ADMINISTRATIVE": 0.10     # Permits/Filing
}

# --- AI AGENT DEFAULTS (Late 2025 Standard) ---
# DeepSeek-V3.2 is the successor to V3 and provides SOTA reasoning-first vision
DEFAULT_MODEL = "deepseek-v3.2" 
REASONING_MODEL = "claude-4.5-sonnet" # Best-in-class for multi-step NYC code reasoning
DEFAULT_CONFIDENCE_THRESHOLD = 0.80 # Tightened for 2025 safety standards
