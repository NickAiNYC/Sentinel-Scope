"""
SentinelScope Exceptions
Custom error hierarchy for robust error handling in NYC construction audits.
"""

class SentinelError(Exception):
    """
    Base exception for all SentinelScope errors.
    Supports custom messaging for Streamlit UI display.
    """
    def __init__(self, message: str = "An internal compliance engine error occurred."):
        self.message = message
        super().__init__(self.message)

class NYCBoundaryError(SentinelError):
    """Raised when coordinates are outside the 5 boroughs of NYC."""
    pass

class AIProviderError(SentinelError):
    """Raised when DeepSeek-V3 or other Vision LLMs fail to respond or return invalid JSON."""
    pass

class GeocodingError(SentinelError):
    """Raised when an address cannot be converted to coordinates."""
    pass

class ComplianceDataError(SentinelError):
    """Raised when the input data (CSV/Image) is malformed or unreadable."""
    pass
