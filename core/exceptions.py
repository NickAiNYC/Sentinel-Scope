class SentinelError(Exception):
    """Base exception for all SentinelScope errors"""
    pass

class NYCBoundaryError(SentinelError):
    """Raised when coordinates are outside the 5 boroughs"""
    pass

class AIProviderError(SentinelError):
    """Raised when DeepSeek or other LLMs fail to respond"""
    pass
