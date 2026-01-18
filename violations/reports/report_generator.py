"""
SentinelScope Pro PDF Report Generator v3.0 (January 2026)
Uses fpdf2 for reliable PDF generation on Streamlit Cloud.
"""

import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from fpdf import FPDF


class SentinelReportGenerator:
    """
    Generates branded PDF reports combining milestone, compliance, and ESG analysis.
    """

    def __init__(
        self,
        project_name: str,
        project_address: str,
        project_type: str,
        auditor_name: str = "John Smith",
        firm_name: str = "ThriveAI Construction Intelligence",
    ):
        self.project_name = project_name
        self.project_address = project_address
        self.project_type = project_type
        self.auditor_name = auditor_name
        self.firm_name = firm_name
        self.report_date = datetime.now().strftime("%B %d, %Y")

    def generate_report(
        self,
        batch_results: list[dict],
        gap_analysis: Any = None,
        include_sustainability: bool = True,
        output_path: str | None = None,
    ) -> str:
        """
        Generate full PDF report using fpdf2.
        Returns path to saved PDF file.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            safe_name = "".join(c for c in self.project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_path = f"reports/SentinelScope_Report_{safe_name}_{timestamp}.pdf"

        os.makedirs("reports", exist_ok=True)

        # Extract data safely
        milestone_classifications = []
        esg_analyses = []
        
        for r in batch_results:
            if r.get("milestone_classification"):
                milestone_classifications.append(r["milestone_classification"])
            if r.get("sustainability_analysis"):
                esg_analyses.append(r["sustainability_analysis"])

        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add first page
        pdf.add_page()
        
        # Header with blue background
        pdf.set_fill_color(30, 64, 175)  # Blue #1e40af
        pdf.rect(0, 0, 210, 40, 'F')
        
        # Title
        pdf.set_font('Arial', 'B', 24)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 10)
        pdf.cell(210, 10, "SentinelScope Pro", 0, 1, 'C')
        
        # Subtitle
        pdf.set_font('Arial', '', 14)
        pdf.set_xy(0, 22)
        pdf.cell(210, 10, "Construction Compliance & Sustainability Audit Report", 0, 1, 'C')
        
        # Project info
        pdf.set_y(60)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Project Information", 0, 1)
        
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Project Name: {self.project_name}", 0, 1)
        pdf.cell(0, 8, f"Address: {self.project_address}", 0, 1)
        pdf.cell(0, 8, f"Type: {self.project_type}", 0, 1)
        pdf.cell(0, 8, f"Audit Date: {self.report_date}", 0, 1)
        pdf.cell(0, 8, f"Auditor: {self.auditor_name}", 0, 1)
        
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Executive Summary", 0, 1)
        
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Images Analyzed: {len(batch_results)}", 0, 1)
        pdf.cell(0, 8, f"Milestones Detected: {len(milestone_classifications)}", 0, 1)
        
        if gap_analysis:
            # Safely get attributes
            compliance_score = getattr(gap_analysis, 'compliance_score', 'N/A')
            risk_score = getattr(gap_analysis, 'risk_score', 'N/A')
            gap_count = getattr(gap_analysis, 'gap_count', 0)
            
            pdf.cell(0, 8, f"Compliance Score: {compliance_score}%", 0, 1)
            pdf.cell(0, 8, f"Risk Score: {risk_score}/100", 0, 1)
            pdf.cell(0, 8, f"Gaps Detected: {gap_count}", 0, 1)
        
        # Sustainability section
        if include_sustainability and esg_analyses:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(124, 58, 237)  # Purple
            pdf.cell(0, 10, "Sustainability Analysis", 0, 1)
            
            high_risks = sum(1 for e in esg_analyses if e.get("energy_risk_level") == "High")
            if high_risks > 0:
                pdf.set_text_color(220, 38, 38)  # Red
                pdf.cell(0, 8, f"⚠️ {high_risks} image(s) with HIGH LL97 energy risk", 0, 1)
            else:
                pdf.set_text_color(5, 150, 105)  # Green
                pdf.cell(0, 8, "✅ No high LL97 energy risks detected", 0, 1)
        
        # Footer
        pdf.set_y(-30)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 5, f"Report Generated by {self.firm_name}", 0, 1, 'C')
        pdf.cell(0, 5, f"Powered by DeepSeek AI Vision • © 2026 ThriveAI", 0, 1, 'C')
        pdf.cell(0, 5, "Confidential • For Internal & Regulatory Use Only", 0, 1, 'C')
        
        # Save PDF
        pdf.output(output_path)
        
        return output_path
