"""
Report generation module - creates evidence tables and summaries
"""

import pandas as pd
from datetime import datetime

def generate_evidence_table(classified_data: pd.DataFrame, gap_analysis: dict) -> str:
    """Generate a markdown evidence table"""
    
    # Create table rows
    table_rows = []
    for _, row in classified_data.iterrows():
        # Create evidence link
        evidence_link = f"[View]({row.get('image_path', '#')})" if row.get('image_path') else "No link"
        
        # Determine if this milestone has gaps
        milestone = row.get('milestone', '')
        has_gap = any(missing.lower() in milestone.lower() 
                     for missing in gap_analysis.get('missing_milestones', []))
        
        table_rows.append({
            "Date": row.get('date', ''),
            "Location": row.get('location', 'Unknown'),
            "Milestone": milestone,
            "System": row.get('system', ''),
            "Evidence": evidence_link,
            "Gap": "⚠️" if has_gap else "✅",
            "Confidence": f"{row.get('confidence', 0)*100:.0f}%"
        })
    
    # Convert to DataFrame for nice formatting
    df_table = pd.DataFrame(table_rows)
    
    # Create markdown report
    report = f"""# Construction Evidence Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project Type: {gap_analysis.get('project_type', 'Unknown')}

## 📊 Compliance Summary
- **Coverage**: {gap_analysis.get('coverage_percentage', 0)}%
- **Risk Level**: {gap_analysis.get('risk_level', 'Unknown')}
- **Missing Milestones**: {gap_analysis.get('gap_count', 0)}
- **Recommendation**: {gap_analysis.get('recommendation', 'Review needed')}

## 🧾 Evidence Table
{df_table.to_markdown(index=False)}

## ⚠️ Action Items
"""
    
    # Add missing milestones
    missing = gap_analysis.get('missing_milestones', [])
    if missing:
        report += "\n**Required documentation missing:**\n"
        for item in missing:
            report += f"- {item}\n"
    else:
        report += "\n✅ All required milestones documented.\n"
    
    return report

def save_report(report_text: str, filename: str = None):
    """Save report to file"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sentinel_report_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(report_text)
    
    print(f"Report saved to {filename}")
    return filename

if __name__ == "__main__":
    # Test report generation
    import pandas as pd
    from gap_detector import detect_gaps
    
    # Create test data
    test_classified = pd.DataFrame([
        {"date": "2025-01-15", "milestone": "MEP Rough-in", "location": "Floor 5", 
         "system": "MEP", "confidence": 0.85, "image_path": "capture1.jpg"},
        {"date": "2025-01-10", "milestone": "Structural Steel", "location": "Floor 4",
         "system": "Structural", "confidence": 0.90, "image_path": "capture2.jpg"}
    ])
    
    test_gaps = detect_gaps(["MEP Rough-in", "Structural Steel"], "structural")
    
    report = generate_evidence_table(test_classified, test_gaps)
    print(report)
    save_report(report)
