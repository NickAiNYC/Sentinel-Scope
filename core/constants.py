"""
SentinelScope Constants v2025.12 (Enhanced)
Hard-coded domain knowledge for NYC Building Code (BC) 2022 + EBC 2025.
Integrated with 2025 Architectural Earth-Tone Design Tokens.

Enhancements:
- NYC BBL validation patterns
- DOB inspector contact info
- Common milestone variations for fuzzy matching
- Permit type mappings
- Cost estimation factors
"""

# ============================================================================
# UI DESIGN TOKENS (2025 Architectural Palette)
# ============================================================================
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
    "INFO_SLATE": "#708090",        # Slate Gray (Neutral)
    "TEXT_CHARCOAL": "#2B2B2B",     # Near Black
}

# Streamlit-compatible CSS classes
STREAMLIT_THEME = {
    "success": "🟢",
    "warning": "🟡", 
    "error": "🔴",
    "info": "🔵",
    "critical": "🚨"
}

# ============================================================================
# NYC GEOGRAPHY & JURISDICTION
# ============================================================================
BOROUGHS = ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"]

# Borough codes (for BBL prefix)
BOROUGH_CODES = {
    "MANHATTAN": "1",
    "BRONX": "2",
    "BROOKLYN": "3",
    "QUEENS": "4",
    "STATEN ISLAND": "5"
}

# BBL (Borough-Block-Lot) validation pattern
BBL_PATTERN = r"^[1-5]\d{9}$"  # Format: 1 digit borough + 5 digits block + 4 digits lot

# NYC DOB Regional Offices
DOB_REGIONAL_OFFICES = {
    "MANHATTAN": {
        "address": "280 Broadway, New York, NY 10007",
        "phone": "(212) 566-5000",
        "hours": "Mon-Fri 8:30 AM - 4:30 PM"
    },
    "BROOKLYN": {
        "address": "210 Joralemon St, Brooklyn, NY 11201",
        "phone": "(718) 643-5290",
        "hours": "Mon-Fri 8:30 AM - 4:30 PM"
    },
    "QUEENS": {
        "address": "120-55 Queens Blvd, Kew Gardens, NY 11424",
        "phone": "(718) 286-4300",
        "hours": "Mon-Fri 8:30 AM - 4:30 PM"
    },
    "BRONX": {
        "address": "1932 Arthur Ave, Bronx, NY 10457",
        "phone": "(718) 579-6400",
        "hours": "Mon-Fri 8:30 AM - 4:30 PM"
    },
    "STATEN ISLAND": {
        "address": "120 Stuyvesant Pl, Staten Island, NY 10301",
        "phone": "(718) 390-5100",
        "hours": "Mon-Fri 8:30 AM - 4:30 PM"
    }
}

# ============================================================================
# NYC BUILDING CODE 2022 & 2025 UPDATES
# ============================================================================
NYC_BC_REFS = {
    "STRUCTURAL": {
        "CHAPTER": "BC Chapter 16",
        "STEEL": "BC Chapter 22",
        "CONCRETE": "BC Chapter 19",
        "FOUNDATIONS": "BC Chapter 18",
        "WOOD": "BC Chapter 23",
        "MASONRY": "BC Chapter 21"
    },
    "FIRE_PROTECTION": {
        "FIRE_RESISTANCE": "BC Chapter 7",
        "PROTECTION_SYSTEMS": "BC Chapter 9",
        "FIREBLOCKING": "BC Section 718",
        "SPRINKLERS": "BC Section 903"
    },
    "MEP": {
        "MECHANICAL": "NYC Mechanical Code Chapter 6",
        "PLUMBING": "NYC Plumbing Code Chapter 7",
        "ELECTRICAL": "NYC Electrical Code (Effective 12/21/2025)",
        "FUEL_GAS": "NYC Fuel Gas Code"
    },
    "SITE_SAFETY": "BC Chapter 33",
    "EXISTING_BUILDING": "NYC EBC (Effective 11/07/2025)", 
    "PARAPETS": "1 RCNY 103-15 (Annual Inspection Rule)",
    "ACCESSIBILITY": "BC Chapter 11 (ADA Compliance)",
    "ENERGY": "NYC Energy Conservation Code (LL97/2019)"
}

# Local Law 97 Carbon Intensity Limits (tCO2e/sqft/year)
LL97_CARBON_LIMITS = {
    "2024-2029": {
        "RESIDENTIAL": 0.00698,
        "COMMERCIAL": 0.00584
    },
    "2030+": {
        "RESIDENTIAL": 0.00357,
        "COMMERCIAL": 0.00453
    }
}

# ============================================================================
# DOB VIOLATION SEVERITY & CLASSES
# ============================================================================
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

DOB_CLASS_RESPONSE_TIMES = {
    "Class C": "24 hours",
    "Class B": "30-45 days",
    "Class A": "90 days"
}

# Common violation types
COMMON_VIOLATIONS = {
    "SITE_SAFETY": ["Missing fence", "Inadequate scaffolding", "No safety plan"],
    "STRUCTURAL": ["Unauthorized work", "No permit", "Unsafe conditions"],
    "FIRE_SAFETY": ["Missing fire extinguisher", "Blocked exit", "Non-compliant sprinkler"],
    "ZONING": ["Illegal conversion", "Exceeds FAR", "Use group violation"]
}

# ============================================================================
# CONSTRUCTION MILESTONES (Phase-Specific)
# ============================================================================
MILESTONES = {
    "EXCAVATION": "Foundation & Earthwork",
    "SUPERSTRUCTURE": "Structural Frame / Superstructure",
    "MEP_ROUGH_IN": "MEP Rough-in",
    "ENCLOSURE": "Building Envelope & Glazing",
    "INTERIOR_FINISH": "Drywall & Interior Finishes",
    "TOP_OUT": "Roofing & Mechanical Bulkhead",
    "FACADE": "Exterior Facade Installation",
    "CORE_SHELL": "Core & Shell Completion",
    "TENANT_FIT_OUT": "Tenant Improvement Work",
    "FINAL_INSPECTION": "Final DOB Sign-Off"
}

# Milestone aliases for fuzzy matching
MILESTONE_ALIASES = {
    "Foundation": ["Foundation Work", "Foundation Complete", "Foundations", "Foundation Pour"],
    "Structural Steel": ["Steel Frame", "Steel Erection", "Steel Work", "Structural Steel Erected"],
    "MEP Rough-in": ["MEP Rough In", "MEP Roughin", "MEP Installation", "MEP Systems"],
    "Fireproofing": ["Fire Proofing", "Fire Protection", "Fireproof Coating"],
    "Drywall Installation": ["Drywall", "Sheetrock", "Gypsum Board", "Drywall Finish"],
    "Exterior Walls": ["Facade", "Building Envelope", "Curtain Wall", "Exterior Cladding"],
    "HVAC Installation": ["HVAC", "Mechanical Systems", "Heating System", "Cooling System"],
    "Electrical Distribution": ["Electrical", "Power Distribution", "Electrical Systems"],
    "Plumbing Rough-in": ["Plumbing", "Plumbing Systems", "Water Lines"],
    "Final Inspection": ["Final DOB", "CO Ready", "Sign-Off", "Certificate of Occupancy"]
}

# ============================================================================
# COMPLIANCE SCORING WEIGHTS (2025 Weights)
# ============================================================================
SCORING_WEIGHTS = {
    "LIFE_SAFETY": 0.40,       # Chapter 33 Site Safety (highest priority)
    "STRUCTURAL": 0.35,        # Foundations/Steel/Concrete
    "ENERGY_EFFICIENCY": 0.15, # LL97 Carbon Compliance
    "ADMINISTRATIVE": 0.10     # Permits/Filing
}

# Risk multipliers by criticality
RISK_MULTIPLIERS = {
    "CRITICAL": 3.0,  # 3x weight for critical items
    "HIGH": 2.0,      # 2x weight for high-priority
    "MEDIUM": 1.0,    # Standard weight
    "LOW": 0.5        # Half weight for low-priority
}

# ============================================================================
# NYC PERMIT TYPES
# ============================================================================
PERMIT_TYPES = {
    "NB": "New Building",
    "A1": "Major Alteration",
    "A2": "Minor Alteration", 
    "A3": "Ordinary Alteration",
    "DM": "Demolition",
    "EQ": "Equipment Work",
    "FN": "Foundation",
    "SG": "Sign",
    "SD": "Standpipe",
    "SP": "Sprinkler",
    "PL": "Plumbing",
    "BL": "Boiler",
    "EW": "Electrical Work"
}

# ============================================================================
# AI AGENT DEFAULTS (Late 2025 Standard)
# ============================================================================
# Using the reasoning-optimized models for forensic auditing
DEFAULT_MODEL = "deepseek-chat"  # Updated to match actual API model name
REASONING_MODEL = "claude-sonnet-4-20250514"  # For complex NYC code analysis
DEFAULT_CONFIDENCE_THRESHOLD = 0.85  # Increased threshold for forensic validation

# Model pricing (as of Dec 2025, per 1K tokens)
MODEL_PRICING = {
    "deepseek-chat": 0.00027,
    "claude-sonnet-4": 0.003,
    "claude-opus-4": 0.015
}

# Vision model settings
VISION_SETTINGS = {
    "temperature": 0.1,        # Low temperature for consistency
    "max_tokens": 1000,        # Sufficient for structured output
    "response_format": "json", # Structured output format
    "timeout": 30              # API timeout (seconds)
}

# ============================================================================
# COST ESTIMATION FACTORS (NYC Average 2025)
# ============================================================================
# Per square foot construction costs by building type
NYC_CONSTRUCTION_COSTS = {
    "RESIDENTIAL_HIGH_RISE": 450,   # $/sqft
    "RESIDENTIAL_MID_RISE": 350,
    "COMMERCIAL_OFFICE": 500,
    "RETAIL": 300,
    "INDUSTRIAL": 200,
    "HOTEL": 550,
    "HOSPITAL": 700
}

# Labor multipliers by borough (Manhattan = 1.0 baseline)
LABOR_MULTIPLIERS = {
    "MANHATTAN": 1.0,
    "BROOKLYN": 0.95,
    "QUEENS": 0.90,
    "BRONX": 0.85,
    "STATEN ISLAND": 0.80
}

# ============================================================================
# AUDIT CONFIGURATION
# ============================================================================
# Default fuzzy matching thresholds
FUZZY_THRESHOLDS = {
    "EXACT_MATCH": 95,        # 95%+ similarity = exact match
    "HIGH_CONFIDENCE": 85,    # 85-94% = high confidence match
    "MEDIUM_CONFIDENCE": 75,  # 75-84% = medium confidence
    "LOW_CONFIDENCE": 70      # 70-74% = low confidence (flagged)
}

# Batch processing limits
BATCH_LIMITS = {
    "MAX_IMAGES": 50,         # Maximum images per batch
    "MAX_WORKERS": 10,        # Maximum parallel threads
    "MAX_RETRIES": 3,         # Maximum API retry attempts
    "TIMEOUT_SECONDS": 30     # Per-image processing timeout
}

# Cache settings
CACHE_SETTINGS = {
    "ENABLE_BY_DEFAULT": True,
    "MAX_CACHE_SIZE_MB": 100,
    "CACHE_TTL_HOURS": 24
}

# ============================================================================
# EXTERNAL API ENDPOINTS
# ============================================================================
NYC_OPEN_DATA_APIS = {
    "DOB_VIOLATIONS": "https://data.cityofnewyork.us/resource/3h2n-5cm9.json",
    "DOB_PERMITS": "https://data.cityofnewyork.us/resource/ipu4-2q9a.json",
    "DOB_COMPLAINTS": "https://data.cityofnewyork.us/resource/eabe-havv.json",
    "PLUTO": "https://data.cityofnewyork.us/resource/64uk-42ks.json"  # Property data
}

DEEPSEEK_API = {
    "base_url": "https://api.deepseek.com",
    "version": "v1"
}

# ============================================================================
# VALIDATION REGEX PATTERNS
# ============================================================================
VALIDATION_PATTERNS = {
    "BBL": r"^[1-5]\d{9}$",                    # 10-digit BBL
    "BIN": r"^\d{7}$",                         # 7-digit Building ID
    "JOB_NUMBER": r"^\d{9}$",                  # 9-digit job/permit number
    "NYC_ADDRESS": r"^\d+\s+[\w\s]+,\s*(?:New York|NY)\s*,?\s*NY\s*\d{5}$"
}

# ============================================================================
# HELP TEXT & DOCUMENTATION
# ============================================================================
HELP_TEXT = {
    "BBL": "Borough-Block-Lot: 10-digit property identifier (e.g., 1012650001)",
    "FUZZY_THRESHOLD": "Minimum similarity score (0-100) for milestone matching",
    "BATCH_PROCESSING": "Process multiple gaps in one API call (60% cost savings)",
    "COMPLIANCE_SCORE": "Percentage of required milestones detected (0-100%)",
    "RISK_SCORE": "Inverse of compliance score - higher = more risk"
}

# ============================================================================
# VERSION INFO
# ============================================================================
VERSION = "2.7.0"
LAST_UPDATED = "2025-01-XX"
NYC_BC_VERSION = "2022 (with 2025 amendments)"
NYC_EBC_VERSION = "2025 (Effective 11/07/2025)"
