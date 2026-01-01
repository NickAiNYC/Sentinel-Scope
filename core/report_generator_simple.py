"""
Simple PDF report generator for testing.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fpdf import FPDF


class SimpleReportGenerator:
    """
    Simple PDF report generator using fpdf2.
    """

    def __init__(
        self,
        project_name: str,
        project_address: str,
        project_type: str,
    ):
        self.project_name = project_name
        self.project_address = project_address
        self.project_type = project_type
        self.report_date = datetime.now().strftime("%B %d, %Y")

    def generate_report(
        self,
        batch_results: List[Dict],
        gap_analysis: Any = None,
        include_sustainability: bool = True,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a simple PDF report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            output_path = f"reports/Test_Report_{timestamp}.pdf"

        os.makedirs("reports", exist_ok=True)

        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Add content
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, "SentinelScope Audit Report", 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f"Project: {self.project_name}", 0, 1)
        pdf.cell(0, 8, f"Address: {self.project_address}", 0, 1)
        pdf.cell(0, 8, f"Type: {self.project_type}", 0, 1)
        pdf.cell(0, 8, f"Date: {self.report_date}", 0, 1)
        pdf.ln(10)
        
        pdf.cell(0, 8, f"Images Analyzed: {len(batch_results)}", 0, 1)
        
        # Save PDF
        pdf.output(output_path)
        
        return output_path
