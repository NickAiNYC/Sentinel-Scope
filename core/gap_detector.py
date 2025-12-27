"""
Gap detection module - identifies missing compliance milestones
"""

def detect_gaps(found_milestones: list, project_type: str = "structural"):
    """Detect missing required milestones for a project type"""
    
    # Required milestones by project type (simplified for MVP)
    requirements = {
        "structural": [
            "Site Preparation",
            "Foundation",
            "Structural Steel", 
            "Decking",
            "Fireproofing",
            "Enclosure"
        ],
        "mep": [
            "MEP Rough-in",
            "Electrical Distribution",
            "Plumbing Rough-in",
            "HVAC Installation",
            "Fire Protection",
            "MEP Trim-out"
        ],
        "interior": [
            "Drywall",
            "Interior Finishes",
            "Flooring",
            "Ceilings",
            "FF&E",
            "Punch List"
        ],
        "commercial": [
            "Shell & Core",
            "Tenant Fit-out",
            "Common Areas",
            "Elevators",
            "Final Inspections"
        ]
    }
    
    # Get requirements for this project type
    required = requirements.get(project_type.lower(), requirements["structural"])
    
    # Normalize milestone names for comparison
    found_normalized = [m.lower() for m in found_milestones]
    required_normalized = [m.lower() for m in required]
    
    # Find missing milestones
    missing = []
    for req, req_norm in zip(required, required_normalized):
        # Check if any found milestone contains this requirement
        found = False
        for found_norm in found_normalized:
            if req_norm in found_norm or found_norm in req_norm:
                found = True
                break
        if not found:
            missing.append(req)
    
    # Calculate coverage
    total_required = len(required)
    total_found = total_required - len(missing)
    coverage = (total_found / total_required) * 100 if total_required > 0 else 0
    
    # Determine risk level
    if coverage >= 90:
        risk_level = "🟢 LOW"
    elif coverage >= 70:
        risk_level = "🟡 MEDIUM"
    else:
        risk_level = "🔴 HIGH"
    
    return {
        "project_type": project_type,
        "required_milestones": required,
        "found_milestones": found_milestones,
        "missing_milestones": missing,
        "total_required": total_required,
        "total_found": total_found,
        "coverage_percentage": round(coverage, 1),
        "gap_count": len(missing),
        "risk_level": risk_level,
        "recommendation": "Complete documentation" if missing else "Evidence sufficient"
    }

if __name__ == "__main__":
    # Test the gap detector
    test_milestones = ["MEP Rough-in", "Structural Steel", "Fireproofing"]
    
    print("Testing gap detection...")
    for project_type in ["structural", "mep", "interior"]:
        result = detect_gaps(test_milestones, project_type)
        print(f"\nProject Type: {project_type}")
        print(f"Coverage: {result['coverage_percentage']}%")
        print(f"Risk: {result['risk_level']}")
        print(f"Missing: {result['missing_milestones']}")
