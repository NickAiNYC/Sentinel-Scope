# Violations Management Module

This module handles NYC DOB violation detection, tracking, and reporting for the SentinelScope AI audit system.

## Directory Structure

### `dob/` - NYC Department of Buildings Violation Integration
Contains modules for fetching and processing NYC DOB violation data:
- `dob_engine.py` - Main DOB violation fetching engine (NYC Open Data API)
- `dob_alerts.py` - DOB alert management and notifications
- `dob_watcher.py` - Permit and violation monitoring

### `reports/` - Violation Report Generation
Modules for generating forensic violation reports:
- `report_generator.py` - Comprehensive violation report generation
- `report_generator_simple.py` - Simplified report generation
- `report.py` - Report models and templates

### `api/` - API Endpoints
REST API endpoints for violation data:
- `violations_router.py` - FastAPI router for violation endpoints

### `evidence/` - Violation Evidence Storage
Directory for storing violation evidence (photos, documents, etc.)

### `templates/` - Report Templates
Templates for violation reports and forms

## Usage Examples

### Fetching DOB Violations
```python
from violations.dob.dob_engine import DOBEngine

# Fetch violations by BBL (Borough-Block-Lot)
violations = DOBEngine.fetch_live_dob_alerts({"bbl": "1012650001"})
print(f"Found {len(violations)} violations")
```

### Monitoring Active Permits
```python
from violations.dob.dob_watcher import get_active_permits

# Check for expiring permits
permits = get_active_permits("3070620001")
print(f"Active permits: {permits}")
```

### Generating Violation Reports
```python
from violations.reports.report_generator import generate_violation_report

# Generate a comprehensive violation report
report = generate_violation_report(
    violations=violations,
    project_name="270 Park Ave Reconstruction",
    address="270 Park Ave, New York, NY"
)
```

## NYC DOB Violation Classification

### Violation Classes:
- **Class A**: Non-hazardous violations (administrative/zoning)
- **Class B**: Hazardous violations (30-45 day remediation required)
- **Class C**: Immediately hazardous violations (24-hour remediation required)

### Common Violation Types:
- Work without permit (BC 105.1)
- Safety - Protection of public (BC 3307)
- Failure to maintain building facade
- Inadequate sidewalk shed illumination

## Data Sources

### NYC Open Data APIs:
1. **DOB Violations**: `https://data.cityofnewyork.us/resource/6bgk-3dad.json`
2. **DOB Complaints**: `https://data.cityofnewyork.us/resource/e9v6-56v6.json`
3. **DOB Permits**: `https://data.cityofnewyork.us/resource/w9ak-ipjd.json`

### Required Credentials:
- NYC Open Data App Token (optional but recommended for higher rate limits)
- BBL (Borough-Block-Lot) number for property identification

## Integration with Main App

The violations module integrates with the main SentinelScope app through:
1. **DOB Engine**: Fetches live violation data during audits
2. **Report Generation**: Creates forensic evidence logs
3. **API Endpoints**: Provides REST API for external systems

## Testing

Run violation-related tests:
```bash
cd ~/sentinel-scope
python -m pytest tests/test_dob_engine.py -v
```

## Adding New Violation Types

To add support for new violation types:
1. Update `dob_engine.py` with new API endpoints
2. Add violation classification logic in `dob_alerts.py`
3. Update report templates in `templates/`
4. Add test cases in the tests directory
