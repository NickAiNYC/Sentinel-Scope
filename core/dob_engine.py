import os

import requests


def fetch_live_dob_alerts(query_params: dict) -> list[dict]:
    """
    Queries NYC OpenData for active DOB ECB Violations using BBL.
    API Documentation: https://dev.socrata.com/foundry/data.cityofnewyork.us/6bgk-3dad
    """
    bbl = query_params.get("bbl")
    if not bbl:
        return []

    # NYC Open Data Endpoint for DOB ECB Violations
    endpoint = "https://data.cityofnewyork.us/resource/6bgk-3dad.json"

    # Check both environment variables and Streamlit secrets for the token
    app_token = os.getenv("NYC_DATA_APP_TOKEN")

    headers = {"X-App-Token": app_token} if app_token else {}

    # Query parameters for Socrata (NYC Open Data)
    params = {
        "bbl": str(bbl),
        "$limit": 10,
        "$order": "issue_date DESC",
        "$select": (
            "violation_number, violation_type, issue_date, "
            "violation_category, respondent_name"
        ),
    }

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Clean up formatting for the UI
            for item in data:
                if "issue_date" in item:
                    # Convert '2023-10-21T00:00:00.000' to '2023-10-21'
                    item["issue_date"] = item["issue_date"][:10]
                if "respondent_name" in item:
                    item["respondent_name"] = str(item["respondent_name"]).title()
            return data
        return []
    except Exception as e:
        print(f"DOB API Error: {e}")
        return []


class DOBEngine:
    """NYC DOB Data Integration Engine wrapper for consistency."""

    @staticmethod
    def fetch_live_dob_alerts(query_params: dict) -> list[dict]:
        """Provides static access to the standalone fetch function."""
        return fetch_live_dob_alerts(query_params)


# Explicitly defining available imports for core/__init__.py
__all__ = ["DOBEngine", "fetch_live_dob_alerts"]
