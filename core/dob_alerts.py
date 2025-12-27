"""
NYC DOB Alerts module - pulls live violation data (placeholder for Day 4)
"""

def get_dob_alerts(lat: float, lon: float, radius_meters: int = 800):
    """Placeholder for NYC DOB alerts API integration"""
    
    # This will be implemented on Day 4 with real NYC Open Data API
    # For now, return mock data
    
    mock_alerts = [
        {
            "date": "2025-01-20",
            "address": "123 Main St",
            "violation_type": "After Hours Work",
            "status": "Open",
            "distance_m": 450
        },
        {
            "date": "2025-01-18", 
            "address": "456 Broadway",
            "violation_type": "Safety Violation",
            "status": "Resolved",
            "distance_m": 620
        }
    ]
    
    return {
        "location": f"{lat}, {lon}",
        "radius_meters": radius_meters,
        "total_alerts": len(mock_alerts),
        "high_risk_count": 1,
        "alerts": mock_alerts,
        "risk_level": "🟡 MEDIUM",
        "message": "Mock data - real NYC DOB API integration coming Day 4"
    }

if __name__ == "__main__":
    # Test with mock coordinates
    alerts = get_dob_alerts(40.6782, -73.9442)
    print("DOB Alerts Test:")
    print(f"Risk Level: {alerts['risk_level']}")
    print(f"Total Alerts: {alerts['total_alerts']}")
    for alert in alerts['alerts']:
        print(f"- {alert['date']}: {alert['violation_type']} ({alert['status']})")
