import os

# API Configurations
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your_fallback_key")
NYC_DATA_APP_TOKEN = os.getenv("NYC_DATA_APP_TOKEN", "")

# Project Constants
DEFAULT_NYC_RADIUS = 800  # Meters
COMPLIANCE_YEAR = 2022    # NYC BC 2022
SUPPORTED_SYSTEMS = ["Structural", "MEP", "Life Safety", "Envelope"]
