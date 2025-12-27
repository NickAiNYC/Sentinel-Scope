"""
Classifier module - tags construction captures by milestone, system, location
"""

def classify_frame(description: str):
    """Classify a single construction frame/capture"""
    desc_lower = description.lower()
    
    # Milestone detection
    if "mep" in desc_lower or "mechanical" in desc_lower or "electrical" in desc_lower:
        milestone = "MEP Rough-in"
        system = "MEP"
        confidence = 0.85
    elif "structural" in desc_lower or "steel" in desc_lower or "beam" in desc_lower:
        milestone = "Structural"
        system = "Structural"
        confidence = 0.90
    elif "fire" in desc_lower or "proofing" in desc_lower:
        milestone = "Fireproofing"
        system = "Fire Protection"
        confidence = 0.88
    elif "drywall" in desc_lower or "gypsum" in desc_lower:
        milestone = "Drywall"
        system = "Interior"
        confidence = 0.80
    elif "window" in desc_lower or "glazing" in desc_lower:
        milestone = "Enclosure"
        system = "Envelope"
        confidence = 0.75
    elif "roof" in desc_lower:
        milestone = "Roofing"
        system = "Envelope"
        confidence = 0.85
    else:
        milestone = "General Construction"
        system = "General"
        confidence = 0.60
    
    # Location detection (simple)
    location = "Unknown"
    if "floor" in desc_lower:
        import re
        floor_match = re.search(r'floor\s*(\d+)', desc_lower)
        if floor_match:
            location = f"Floor {floor_match.group(1)}"
    
    return {
        "milestone": milestone,
        "system": system,
        "location": location,
        "confidence": confidence
    }

def batch_classify(dataframe):
    """Classify multiple frames in a DataFrame"""
    import pandas as pd
    
    results = []
    for _, row in dataframe.iterrows():
        tags = classify_frame(str(row.get('description', '')))
        result = {
            'date': row.get('date', ''),
            'description': row.get('description', ''),
            'image_path': row.get('image_path', ''),
            **tags
        }
        results.append(result)
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test the classifier
    import pandas as pd
    
    test_data = pd.DataFrame([
        {"date": "2025-01-15", "description": "MEP rough-in inspection floor 5", "image_path": "capture1.jpg"},
        {"date": "2025-01-10", "description": "Structural steel installation", "image_path": "capture2.jpg"},
        {"date": "2025-01-05", "description": "Fireproofing application on columns", "image_path": "capture3.jpg"}
    ])
    
    print("Testing classifier...")
    classified = batch_classify(test_data)
    print("\nClassification Results:")
    print(classified.to_string())
