import os
from dotenv import load_dotenv

# Load local .env file if it exists (for your Mac)
load_dotenv()

# API Configurations
# Using None as default makes it easier to check for missing keys
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
NYC_DATA_APP_TOKEN = os.getenv("NYC_DATA_APP_TOKEN")

# DeepSeek Specifics
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # or "deepseek-reasoner" for R1

# Project Constants
DEFAULT_NYC_RADIUS = 800    # Meters
COMPLIANCE_YEAR = 2022      # NYC BC 2022
SUPPORTED_SYSTEMS = ["Structural", "MEP", "Life Safety", "Envelope"]

# Validation (Optional but helpful for debugging)
if not DEEPSEEK_API_KEY:
    print("⚠️ WARNING: DEEPSEEK_API_KEY is not set in environment.")
