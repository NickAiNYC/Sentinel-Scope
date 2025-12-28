"""
SentinelScope Utility Functions v2.7
Helper functions for common operations across the application.

Categories:
- Data validation and sanitization
- NYC-specific utilities (BBL, borough, address)
- File handling and image processing
- Date/time utilities
- Cost estimation
- Reporting helpers
- API error handling
"""
import re
import hashlib
import base64
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from pathlib import Path
import json

# Optional imports with fallbacks
try:
    from PIL import Image
    import io
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    from core.constants import (
        BOROUGH_CODES,
        VALIDATION_PATTERNS,
        NYC_CONSTRUCTION_COSTS,
        LABOR_MULTIPLIERS,
        DOB_REGIONAL_OFFICES
    )
except ImportError:
    # Fallback values
    BOROUGH_CODES = {"MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3", "QUEENS": "4", "STATEN ISLAND": "5"}
    VALIDATION_PATTERNS = {"BBL": r"^[1-5]\d{9}$"}
    NYC_CONSTRUCTION_COSTS = {"RESIDENTIAL_HIGH_RISE": 450}
    LABOR_MULTIPLIERS = {"MANHATTAN": 1.0, "BROOKLYN": 0.95}
    DOB_REGIONAL_OFFICES = {}


# ============================================================================
# NYC-SPECIFIC UTILITIES
# ============================================================================

def validate_bbl(bbl: str) -> bool:
    """
    Validate NYC Borough-Block-Lot (BBL) format.
    
    Args:
        bbl: 10-digit BBL string
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_bbl("1012650001")
        True
        >>> validate_bbl("123456")
        False
    """
    if not bbl or not isinstance(bbl, str):
        return False
    
    pattern = VALIDATION_PATTERNS.get("BBL", r"^[1-5]\d{9}$")
    return bool(re.match(pattern, bbl.strip()))


def parse_bbl(bbl: str) -> Optional[Dict[str, str]]:
    """
    Parse BBL into components (borough, block, lot).
    
    Args:
        bbl: 10-digit BBL string
        
    Returns:
        Dictionary with parsed components or None if invalid
        
    Examples:
        >>> parse_bbl("1012650001")
        {
            'bbl': '1012650001',
            'borough_code': '1',
            'borough_name': 'MANHATTAN',
            'block': '01265',
            'lot': '0001'
        }
    """
    if not validate_bbl(bbl):
        return None
    
    bbl = bbl.strip()
    
    borough_map = {
        "1": "MANHATTAN",
        "2": "BRONX",
        "3": "BROOKLYN",
        "4": "QUEENS",
        "5": "STATEN ISLAND"
    }
    
    return {
        "bbl": bbl,
        "borough_code": bbl[0],
        "borough_name": borough_map.get(bbl[0], "UNKNOWN"),
        "block": bbl[1:6],
        "lot": bbl[6:10]
    }


def format_bbl(borough: str, block: str, lot: str) -> Optional[str]:
    """
    Format borough, block, and lot into BBL string.
    
    Args:
        borough: Borough name or code (e.g., "MANHATTAN" or "1")
        block: 5-digit block number
        lot: 4-digit lot number
        
    Returns:
        Formatted BBL string or None if invalid
        
    Examples:
        >>> format_bbl("MANHATTAN", "01265", "0001")
        "1012650001"
        >>> format_bbl("1", "1265", "1")
        "1012650001"
    """
    # Get borough code
    if len(borough) == 1 and borough in "12345":
        borough_code = borough
    else:
        borough_code = BOROUGH_CODES.get(borough.upper())
        if not borough_code:
            return None
    
    # Pad block and lot
    block_padded = str(block).zfill(5)
    lot_padded = str(lot).zfill(4)
    
    # Validate lengths
    if len(block_padded) != 5 or len(lot_padded) != 4:
        return None
    
    bbl = f"{borough_code}{block_padded}{lot_padded}"
    
    return bbl if validate_bbl(bbl) else None


def get_dob_office_info(borough: str) -> Optional[Dict[str, str]]:
    """
    Get DOB regional office contact information for a borough.
    
    Args:
        borough: Borough name (e.g., "MANHATTAN", "BROOKLYN")
        
    Returns:
        Dictionary with office details or None if not found
    """
    return DOB_REGIONAL_OFFICES.get(borough.upper())


def normalize_address(address: str) -> str:
    """
    Normalize NYC address format for consistency.
    
    Args:
        address: Raw address string
        
    Returns:
        Normalized address string
        
    Examples:
        >>> normalize_address("270 park ave new york ny")
        "270 Park Ave, New York, NY"
    """
    # Remove extra whitespace
    address = " ".join(address.split())
    
    # Capitalize each word
    address = address.title()
    
    # Fix common abbreviations
    replacements = {
        " Ave ": " Ave, ",
        " St ": " St, ",
        " Rd ": " Rd, ",
        " Blvd ": " Blvd, ",
        " New York Ny": " New York, NY",
        " Ny ": " NY ",
        "Nyc": "NYC"
    }
    
    for old, new in replacements.items():
        address = address.replace(old, new)
    
    return address


# ============================================================================
# FILE AND IMAGE UTILITIES
# ============================================================================

def get_file_hash(file_content: bytes) -> str:
    """
    Generate SHA-256 hash of file content.
    
    Args:
        file_content: Raw file bytes
        
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(file_content).hexdigest()


def encode_image_to_base64(image_source: Union[str, bytes, Any]) -> str:
    """
    Encode image to base64 string for API transmission.
    
    Args:
        image_source: File path, bytes, or file-like object
        
    Returns:
        Base64-encoded string
        
    Raises:
        IOError: If encoding fails
    """
    try:
        # Handle file-like objects (Streamlit UploadedFile)
        if hasattr(image_source, 'read'):
            image_source.seek(0)
            content = image_source.read()
            return base64.b64encode(content).decode('utf-8')
        
        # Handle bytes
        if isinstance(image_source, bytes):
            return base64.b64encode(image_source).decode('utf-8')
        
        # Handle file path
        with open(image_source, 'rb') as f:
            content = f.read()
            return base64.b64encode(content).decode('utf-8')
    
    except Exception as e:
        raise IOError(f"Failed to encode image: {str(e)}")


def get_image_metadata(image_source: Union[str, bytes, Any]) -> Dict[str, Any]:
    """
    Extract metadata from image (size, format, dimensions).
    
    Args:
        image_source: File path, bytes, or file-like object
        
    Returns:
        Dictionary with image metadata
    """
    if not PILLOW_AVAILABLE:
        return {"error": "PIL not available"}
    
    try:
        # Handle different input types
        if hasattr(image_source, 'read'):
            image_source.seek(0)
            img = Image.open(image_source)
        elif isinstance(image_source, bytes):
            img = Image.open(io.BytesIO(image_source))
        else:
            img = Image.open(image_source)
        
        return {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "size_bytes": len(img.tobytes()) if hasattr(img, 'tobytes') else None
        }
    
    except Exception as e:
        return {"error": str(e)}


def validate_image_file(file_path: str, max_size_mb: int = 10) -> tuple[bool, str]:
    """
    Validate image file (exists, correct format, size).
    
    Args:
        file_path: Path to image file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check existence
    if not path.exists():
        return False, "File does not exist"
    
    # Check size
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)"
    
    # Check format
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid format: {path.suffix} (allowed: {valid_extensions})"
    
    return True, ""


# ============================================================================
# DATE AND TIME UTILITIES
# ============================================================================

def format_timestamp(dt: datetime, format: str = "display") -> str:
    """
    Format datetime for various use cases.
    
    Args:
        dt: Datetime object
        format: Format type ('display', 'filename', 'api', 'relative')
        
    Returns:
        Formatted string
        
    Examples:
        >>> format_timestamp(datetime.now(), 'display')
        "Dec 28, 2025 3:45 PM"
        >>> format_timestamp(datetime.now(), 'filename')
        "20251228_154530"
    """
    formats = {
        "display": "%b %d, %Y %I:%M %p",
        "filename": "%Y%m%d_%H%M%S",
        "api": "%Y-%m-%dT%H:%M:%S",
        "date_only": "%Y-%m-%d",
        "time_only": "%I:%M %p"
    }
    
    if format == "relative":
        return get_relative_time(dt)
    
    return dt.strftime(formats.get(format, formats["display"]))


def get_relative_time(dt: datetime) -> str:
    """
    Get human-readable relative time (e.g., "2 hours ago").
    
    Args:
        dt: Datetime object
        
    Returns:
        Relative time string
    """
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def calculate_deadline(risk_level: str) -> datetime:
    """
    Calculate remediation deadline based on risk level.
    
    Args:
        risk_level: "Critical", "High", "Medium", or "Low"
        
    Returns:
        Deadline datetime
    """
    now = datetime.now()
    
    deadlines = {
        "Critical": timedelta(hours=24),
        "High": timedelta(days=7),
        "Medium": timedelta(days=30),
        "Low": timedelta(days=90)
    }
    
    return now + deadlines.get(risk_level, timedelta(days=30))


# ============================================================================
# COST ESTIMATION UTILITIES
# ============================================================================

def estimate_construction_cost(
    sqft: float,
    building_type: str,
    borough: str = "MANHATTAN"
) -> Dict[str, float]:
    """
    Estimate construction cost for NYC project.
    
    Args:
        sqft: Square footage
        building_type: Type from NYC_CONSTRUCTION_COSTS
        borough: NYC borough name
        
    Returns:
        Dictionary with cost breakdown
        
    Examples:
        >>> estimate_construction_cost(10000, "RESIDENTIAL_HIGH_RISE", "BROOKLYN")
        {
            'base_cost_per_sqft': 450.0,
            'labor_multiplier': 0.95,
            'adjusted_cost_per_sqft': 427.5,
            'total_cost': 4275000.0
        }
    """
    base_cost = NYC_CONSTRUCTION_COSTS.get(building_type, 400)
    labor_mult = LABOR_MULTIPLIERS.get(borough.upper(), 1.0)
    
    adjusted_cost = base_cost * labor_mult
    total_cost = sqft * adjusted_cost
    
    return {
        "base_cost_per_sqft": base_cost,
        "labor_multiplier": labor_mult,
        "adjusted_cost_per_sqft": adjusted_cost,
        "total_cost": total_cost,
        "total_cost_formatted": format_currency(total_cost)
    }


def estimate_remediation_cost(
    gap_count: int,
    risk_level: str,
    building_type: str = "RESIDENTIAL_HIGH_RISE"
) -> float:
    """
    Estimate cost to remediate compliance gaps.
    
    Args:
        gap_count: Number of gaps
        risk_level: Average risk level
        building_type: Building type
        
    Returns:
        Estimated remediation cost (USD)
    """
    # Base cost per gap by risk level
    base_costs = {
        "Critical": 50000,
        "High": 20000,
        "Medium": 5000,
        "Low": 1000
    }
    
    base = base_costs.get(risk_level, 5000)
    
    # Building type multiplier
    type_multipliers = {
        "RESIDENTIAL_HIGH_RISE": 1.2,
        "COMMERCIAL_OFFICE": 1.5,
        "HOSPITAL": 2.0,
        "INDUSTRIAL": 0.8
    }
    
    multiplier = type_multipliers.get(building_type, 1.0)
    
    return gap_count * base * multiplier


def format_currency(amount: float, include_cents: bool = False) -> str:
    """
    Format number as USD currency.
    
    Args:
        amount: Dollar amount
        include_cents: Whether to include cents
        
    Returns:
        Formatted currency string
        
    Examples:
        >>> format_currency(1234567.89)
        "$1,234,568"
        >>> format_currency(1234.56, include_cents=True)
        "$1,234.56"
    """
    if include_cents:
        return f"${amount:,.2f}"
    else:
        return f"${amount:,.0f}"


# ============================================================================
# DATA VALIDATION AND SANITIZATION
# ============================================================================

def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        max_length: Maximum length
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename or "unnamed_file"


def validate_json_structure(data: Union[str, dict], required_keys: List[str]) -> tuple[bool, str]:
    """
    Validate JSON structure has required keys.
    
    Args:
        data: JSON string or dict
        required_keys: List of required key names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            return False, f"Missing required keys: {', '.join(missing_keys)}"
        
        return True, ""
    
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text for consistent processing.
    
    Args:
        text: Input text
        max_length: Optional maximum length
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text.strip()


# ============================================================================
# API ERROR HANDLING
# ============================================================================

def parse_api_error(error: Exception) -> Dict[str, str]:
    """
    Parse API error into structured format.
    
    Args:
        error: Exception from API call
        
    Returns:
        Dictionary with error details
    """
    error_str = str(error).lower()
    
    # Categorize error
    if "rate_limit" in error_str or "429" in error_str:
        category = "rate_limit"
        message = "API rate limit exceeded. Please wait and try again."
        suggestion = "Wait 60 seconds or reduce batch size."
    
    elif "api_key" in error_str or "401" in error_str or "authentication" in error_str:
        category = "authentication"
        message = "Invalid API key or authentication failed."
        suggestion = "Check your API key in Settings."
    
    elif "timeout" in error_str or "connection" in error_str:
        category = "network"
        message = "Network connection timeout."
        suggestion = "Check internet connection and try again."
    
    elif "json" in error_str or "parse" in error_str:
        category = "parsing"
        message = "Failed to parse API response."
        suggestion = "This may be a temporary issue. Try again."
    
    else:
        category = "unknown"
        message = f"API error: {str(error)[:200]}"
        suggestion = "If this persists, contact support."
    
    return {
        "category": category,
        "message": message,
        "suggestion": suggestion,
        "raw_error": str(error)
    }


def format_error_for_ui(error: Exception) -> str:
    """
    Format error for user-friendly display in Streamlit.
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error message
    """
    error_info = parse_api_error(error)
    
    emoji_map = {
        "rate_limit": "⏸️",
        "authentication": "🔑",
        "network": "🔌",
        "parsing": "📋",
        "unknown": "⚠️"
    }
    
    emoji = emoji_map.get(error_info["category"], "⚠️")
    
    return (
        f"{emoji} **{error_info['message']}**\n\n"
        f"💡 *Suggestion: {error_info['suggestion']}*"
    )


# ============================================================================
# REPORTING HELPERS
# ============================================================================

def generate_report_filename(
    project_name: str,
    report_type: str = "compliance",
    extension: str = "pdf"
) -> str:
    """
    Generate standardized report filename.
    
    Args:
        project_name: Project identifier
        report_type: Type of report
        extension: File extension
        
    Returns:
        Filename string
        
    Examples:
        >>> generate_report_filename("Hudson Yards", "compliance", "pdf")
        "Hudson_Yards_compliance_20251228_154530.pdf"
    """
    # Sanitize project name
    safe_name = sanitize_filename(project_name).replace(' ', '_')
    
    # Add timestamp
    timestamp = format_timestamp(datetime.now(), 'filename')
    
    return f"{safe_name}_{report_type}_{timestamp}.{extension}"


def calculate_compliance_grade(score: int) -> str:
    """
    Convert compliance score to letter grade.
    
    Args:
        score: Compliance score (0-100)
        
    Returns:
        Letter grade (A+ to F)
    """
    if score >= 98:
        return "A+"
    elif score >= 93:
        return "A"
    elif score >= 90:
        return "A-"
    elif score >= 87:
        return "B+"
    elif score >= 83:
        return "B"
    elif score >= 80:
        return "B-"
    elif score >= 77:
        return "C+"
    elif score >= 73:
        return "C"
    elif score >= 70:
        return "C-"
    elif score >= 67:
        return "D+"
    elif score >= 63:
        return "D"
    elif score >= 60:
        return "D-"
    else:
        return "F"


def get_status_emoji(status: str) -> str:
    """
    Get emoji for status indicators.
    
    Args:
        status: Status string
        
    Returns:
        Emoji character
    """
    emoji_map = {
        "EXCELLENT": "🌟",
        "COMPLIANT": "✅",
        "ACCEPTABLE": "👍",
        "NEEDS ATTENTION": "⚠️",
        "NON-COMPLIANT": "🚨",
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    
    return emoji_map.get(status.upper(), "❓")
