#!/usr/bin/env python3
"""
Test script for SentinelScope
"""

import sys
import os
sys.path.append('core')

def test_all():
    print("🧪 Testing SentinelScope...")
    print("=" * 50)
    
    # 1. Test imports
    try:
        import pandas as pd
        from classifier import batch_classify
        from gap_detector import detect_gaps
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # 2. Test classifier
    print("\n1. Testing Classifier...")
    test_data = pd.DataFrame([
        {'date': '2025-01-15', 'description': 'MEP rough-in inspection', 'image_path': 'test1.jpg'},
        {'date': '2025-01-10', 'description': 'Structural steel beam installation', 'image_path': 'test2.jpg'},
    ])
    classified = batch_classify(test_data)
    print(f"   Classified {len(classified)} records")
    print(f"   Sample: {classified.iloc[0]['milestone']} ({classified.iloc[0]['confidence']*100:.0f}% confidence)")
    
    # 3. Test gap detection
    print("\n2. Testing Gap Detection...")
    milestones = classified['milestone'].tolist()
    gaps = detect_gaps(milestones, 'structural')
    print(f"   Coverage: {gaps['coverage_percentage']}%")
    print(f"   Risk Level: {gaps['risk_level']}")
    
    print("\n" + "=" * 50)
    print("✅ Day 1 MVP complete!")
    print("\nNext: Run 'streamlit run app.py' to launch dashboard")

if __name__ == "__main__":
    test_all()
