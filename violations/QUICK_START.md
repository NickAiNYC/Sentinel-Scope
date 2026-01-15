# Violations Module - Quick Start

## Overview
The violations module handles NYC DOB violation detection, tracking, and reporting.

## Basic Usage

### 1. Fetch DOB Violations
```python
from violations.dob.dob_engine import DOBEngine

# Fetch violations by BBL
violations = DOBEngine.fetch_live_dob_alerts({"bbl": "1012650001"})
print(f"Found {len(violations)} violations")

# Sample output structure:
# [
#   {
#     "violation_number": "V123456",
#     "violation_type": "Work Without Permit",
#     "issue_date": "2024-01-15",
#     "violation_category": "BC 105.1",
#     "respondent_name": "Contractor Name"
#   }
# ]
```

### 2. Monitor Active Permits
```python
from violations.dob.dob_watcher import get_active_permits

permits = get_active_permits("3070620001")
print(f"Active permits: {permits}")
```

### 3. Generate Violation Reports
```python
from violations.reports.report_generator import generate_violation_report

# Note: You may need to adapt this based on the actual function signature
report = generate_violation_report(
    violations=violations,
    project_name="Test Project",
    address="123 Main St, NYC"
)
```

## Integration with Main App

The violations module is already integrated into the main SentinelScope app:

1. **During audit execution**: DOB violations are fetched automatically
2. **In the dashboard**: Violations displayed in "NYC DOB Sync" tab
3. **In reports**: Violations included in forensic evidence logs

## API Endpoints

FastAPI router available at `violations/api/violations_router.py`:

```python
# Example endpoints:
# GET /violations/bbl/{bbl}     # Get violations by BBL
# GET /violations/search        # Search violations by address
```

## Adding New Violation Types

1. **Update `dob_engine.py`**: Add new API endpoints
2. **Update `dob_alerts.py`**: Add classification logic
3. **Update report templates**: In `violations/templates/`
4. **Add tests**: In the main `tests/` directory

## Data Sources

- **NYC Open Data API**: https://data.cityofnewyork.us/
- **DOB Violations**: Resource ID `6bgk-3dad`
- **DOB Complaints**: Resource ID `e9v6-56v6`
- **DOB Permits**: Resource ID `w9ak-ipjd`

## NYC DOB Violation Classes

- **Class A**: Non-hazardous (administrative)
- **Class B**: Hazardous (30-45 day remediation)
- **Class C**: Immediately hazardous (24-hour remediation)

## Testing

```bash
# Run existing tests
cd ~/sentinel-scope
python -m pytest tests/

# Test violation imports
python -c "from violations.dob.dob_engine import DOBEngine; print('OK')"
```
