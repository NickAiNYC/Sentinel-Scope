"""
SentinelScope Pro PDF Report Generator v3.0 (January 2026)
Generates beautiful, client-ready compliance + sustainability reports.
Uses fpdf2 for reliable PDF generation on Streamlit Cloud.
"""

import os
from collections import Counter
from datetime import datetime
from typing import Any

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
        gap_analysis: Any,
        include_sustainability: bool = True,
        output_path: str | None = None,
    ) -> str:
        """
        Generate full PDF report using fpdf2.
        Returns path to saved PDF file.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            safe_name = "".join(
                c for c in self.project_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            output_path = f"reports/SentinelScope_Report_{safe_name}_{timestamp}.pdf"

        os.makedirs("reports", exist_ok=True)

        # Extract data
        milestone_classifications = [
            r.get("milestone_classification")
            for r in batch_results
            if r.get("milestone_classification")
        ]
        esg_analyses = [
            r.get("sustainability_analysis")
            for r in batch_results
            if r.get("sustainability_analysis")
        ]

        high_esg_risks = sum(
            1 for e in esg_analyses if e and e.get("energy_risk_level") == "High"
        )

        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Add first page
        pdf.add_page()

        # Header
        self._add_header(pdf)

        # Project info
        self._add_project_info(pdf)

        # Executive Summary
        if gap_analysis:
            compliance_score = getattr(gap_analysis, "compliance_score", 0)
            risk_score = getattr(gap_analysis, "risk_score", 0)
            gap_count = getattr(gap_analysis, "gap_count", 0)
            next_priority = getattr(gap_analysis, "next_priority", "Unknown")

            self._add_executive_summary(
                pdf,
                compliance_score,
                risk_score,
                gap_count,
                next_priority,
                len(batch_results),
                len(milestone_classifications),
                high_esg_risks,
                include_sustainability,
            )
        else:
            self._add_fallback_summary(
                pdf, len(batch_results), len(milestone_classifications)
            )

        # Compliance Section
        if gap_analysis:
            self._add_compliance_section(pdf, gap_analysis)

        # ESG Section
        if include_sustainability and esg_analyses:
            self._add_esg_section(pdf, esg_analyses)

        # Photo Summary
        self._add_photo_summary(pdf, len(batch_results), milestone_classifications)

        # Footer
        self._add_footer(pdf)

        # Save PDF
        pdf.output(output_path)

        return output_path

    def _add_header(self, pdf: FPDF):
        """Add header with blue background"""
        # Blue header rectangle
        pdf.set_fill_color(30, 64, 175)  # Blue #1e40af
        pdf.rect(0, 0, 210, 50, "F")

        # Title
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 10)
        pdf.cell(210, 10, "SentinelScope Pro", 0, 1, "C")

        # Subtitle
        pdf.set_font("Helvetica", "", 14)
        pdf.set_xy(0, 25)
        pdf.cell(
            210, 10, "Construction Compliance & Sustainability Audit Report", 0, 1, "C"
        )

    def _add_project_info(self, pdf: FPDF):
        """Add project information section"""
        pdf.set_y(60)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "Project Information", 0, 1)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Project Name: {self.project_name}", 0, 1)
        pdf.cell(0, 8, f"Address: {self.project_address}", 0, 1)
        pdf.cell(0, 8, f"Type: {self.project_type}", 0, 1)
        pdf.cell(0, 8, f"Audit Date: {self.report_date}", 0, 1)
        pdf.cell(0, 8, f"Auditor: {self.auditor_name}", 0, 1)

        pdf.ln(10)

    def _add_executive_summary(
        self,
        pdf: FPDF,
        compliance_score: int,
        risk_score: int,
        gap_count: int,
        next_priority: str,
        total_images: int,
        classified_images: int,
        high_esg_risks: int,
        include_sustainability: bool,
    ):
        """Add executive summary with metrics"""
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "📋 Executive Summary", 0, 1)

        # Add a line
        pdf.set_draw_color(59, 130, 246)  # Blue #3b82f6
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Metrics in boxes
        pdf.set_y(pdf.get_y())

        # Compliance Score box
        self._add_metric_box(
            pdf, "Compliance Score", f"{compliance_score}%", (30, 64, 175), x=10
        )

        # Risk Score box
        risk_color = (5, 150, 105) if risk_score < 30 else (220, 38, 38)
        self._add_metric_box(pdf, "Risk Score", f"{risk_score}/100", risk_color, x=60)

        # Gaps Detected box
        self._add_metric_box(pdf, "Gaps", str(gap_count), (245, 158, 66), x=110)

        # Images Analyzed box
        self._add_metric_box(pdf, "Images", str(total_images), (124, 58, 237), x=160)

        pdf.ln(25)

        # Summary text
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Status: {next_priority}", 0, 1)
        pdf.cell(0, 8, f"{gap_count} compliance gap(s) detected", 0, 1)
        pdf.cell(0, 8, f"{classified_images} images classified with milestones", 0, 1)

        if include_sustainability:
            if high_esg_risks > 0:
                pdf.set_text_color(220, 38, 38)
                pdf.cell(
                    0,
                    8,
                    f"⚠️ {high_esg_risks} image(s) with HIGH Local Law 97 risk",
                    0,
                    1,
                )
            else:
                pdf.set_text_color(5, 150, 105)
                pdf.cell(0, 8, "✅ No high LL97 energy risks detected", 0, 1)

        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

    def _add_fallback_summary(
        self, pdf: FPDF, total_images: int, classified_images: int
    ):
        """Fallback summary when gap_analysis is not available"""
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "📋 Executive Summary", 0, 1)

        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Images Analyzed: {total_images}", 0, 1)
        pdf.cell(0, 8, f"Images Classified: {classified_images}", 0, 1)
        pdf.cell(0, 8, "Note: Compliance analysis not available", 0, 1)
        pdf.ln(10)

    def _add_metric_box(
        self, pdf: FPDF, label: str, value: str, color: tuple, x: float
    ):
        """Add a metric box at position x"""
        y = pdf.get_y()

        # Draw colored box
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 40, 25, "F")

        # Value (centered)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_xy(x + 5, y + 5)
        pdf.cell(30, 8, str(value), 0, 0, "C")

        # Label (centered below)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(x, y + 16)
        pdf.cell(40, 6, label, 0, 0, "C")

        # Reset text color
        pdf.set_text_color(0, 0, 0)

    def _add_compliance_section(self, pdf: FPDF, gap_analysis: Any):
        """Add compliance analysis section"""
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "🛡️ DOB Milestone & Compliance Analysis", 0, 1)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        compliance_score = getattr(gap_analysis, "compliance_score", 0)
        total_found = getattr(gap_analysis, "total_found", 0)
        missing_milestones = getattr(gap_analysis, "missing_milestones", [])

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Overall Compliance: {compliance_score}%", 0, 1)
        pdf.cell(
            0,
            8,
            (
                f"Found: {total_found} milestones • "
                f"Missing: {len(missing_milestones)} milestones"
            ),
            0,
            1,
        )

        pdf.ln(5)

        if missing_milestones:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, f"{len(missing_milestones)} Compliance Gap(s):", 0, 1)
            pdf.ln(3)

            # Table header
            pdf.set_fill_color(243, 244, 246)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(70, 8, "Missing Milestone", 1, 0, "C", fill=True)
            pdf.cell(25, 8, "DOB Code", 1, 0, "C", fill=True)
            pdf.cell(30, 8, "Risk Level", 1, 0, "C", fill=True)
            pdf.cell(25, 8, "Class", 1, 0, "C", fill=True)
            pdf.cell(40, 8, "Deadline", 1, 1, "C", fill=True)

            # Table rows
            pdf.set_font("Helvetica", "", 9)
            for gap in missing_milestones[:10]:  # Limit to 10 gaps
                # Safely access gap attributes
                milestone = getattr(gap, "milestone", "Unknown")[:30]
                dob_code = getattr(gap, "dob_code", "N/A")
                risk_level = getattr(gap, "risk_level", "Unknown")
                dob_class = getattr(gap, "dob_class", "N/A")
                deadline = getattr(gap, "deadline", "N/A")

                pdf.cell(70, 8, milestone, 1)
                pdf.cell(25, 8, dob_code, 1)

                # Color code risk level
                risk_colors = {
                    "Critical": (220, 38, 38),
                    "High": (249, 115, 22),
                    "Medium": (217, 119, 6),
                    "Low": (5, 150, 105),
                }
                color = risk_colors.get(risk_level, (107, 114, 128))
                pdf.set_text_color(*color)
                pdf.cell(30, 8, risk_level, 1)
                pdf.set_text_color(0, 0, 0)

                pdf.cell(25, 8, dob_class, 1)
                pdf.cell(40, 8, deadline, 1)
                pdf.ln()
        else:
            pdf.set_text_color(5, 150, 105)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(
                0, 10, "✅ No compliance gaps detected. Excellent documentation!", 0, 1
            )
            pdf.set_text_color(0, 0, 0)

        pdf.ln(10)

    def _add_esg_section(self, pdf: FPDF, esg_analyses: list[dict]):
        """Add ESG/LL97 analysis section"""
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(124, 58, 237)  # Purple #7c3aed
        pdf.cell(0, 10, "🌿 Sustainability & Local Law 97 Analysis", 0, 1)
        pdf.set_draw_color(124, 58, 237)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(
            0,
            8,
            (
                f"Visual energy efficiency assessment performed on "
                f"{len(esg_analyses)} images."
            ),
            0,
            1,
        )

        # Count risk levels
        risk_counts = Counter(
            a.get("energy_risk_level", "Unknown") for a in esg_analyses if a
        )

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Risk Level Distribution:", 0, 1)

        for risk, count in risk_counts.items():
            pdf.set_font("Helvetica", "", 11)
            if risk == "High":
                pdf.set_text_color(220, 38, 38)
                pdf.cell(0, 7, f"  • {risk}: {count} image(s) ⚠️", 0, 1)
            elif risk == "Medium":
                pdf.set_text_color(217, 119, 6)
                pdf.cell(0, 7, f"  • {risk}: {count} image(s)", 0, 1)
            elif risk == "Low":
                pdf.set_text_color(5, 150, 105)
                pdf.cell(0, 7, f"  • {risk}: {count} image(s) ✅", 0, 1)
            else:
                pdf.set_text_color(107, 114, 128)
                pdf.cell(0, 7, f"  • {risk}: {count} image(s)", 0, 1)

        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

        # Key recommendations
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Key Recommendations:", 0, 1)

        recommendations = set()
        for analysis in esg_analyses:
            if analysis:
                for rec in analysis.get("recommendations", [])[:2]:
                    if rec:
                        recommendations.add(rec)

        pdf.set_font("Helvetica", "", 11)
        for i, rec in enumerate(list(recommendations)[:5], 1):
            pdf.cell(10, 7, "")
            pdf.multi_cell(0, 7, f"{i}. {rec}")

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(124, 58, 237)
        pdf.cell(
            0,
            8,
            (
                "Recommendation: Consider professional energy audit for "
                "full LL97 decarbonization planning."
            ),
            0,
            1,
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

    def _add_photo_summary(
        self, pdf: FPDF, total_images: int, milestone_classifications: list
    ):
        """Add photo analysis summary"""
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, "📸 Photo Intelligence Summary", 0, 1)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(
            0,
            8,
            f"{total_images} site photos processed using DeepSeek-VL multimodal AI.",
            0,
            1,
        )

        if milestone_classifications:
            milestones = []
            for mc in milestone_classifications:
                if mc and hasattr(mc, "milestone"):
                    milestones.append(mc.milestone)
                elif mc and isinstance(mc, dict) and "milestone" in mc:
                    milestones.append(mc["milestone"])

            if milestones:
                milestone_counts = Counter(milestones)
                pdf.cell(0, 8, "Detected milestones:", 0, 1)

                for milestone, count in milestone_counts.items():
                    pdf.cell(20, 7, "")
                    pdf.cell(0, 7, f"• {milestone}: {count} image(s)", 0, 1)
            else:
                pdf.cell(0, 8, "No milestones classified in images", 0, 1)
        else:
            pdf.cell(0, 8, "No milestone classifications available", 0, 1)

        pdf.ln(10)

    def _add_footer(self, pdf: FPDF):
        """Add footer to all pages"""
        # Set footer position
        pdf.set_y(-30)

        # Footer text
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(107, 114, 128)

        pdf.cell(0, 5, f"Report Generated by {self.firm_name}", 0, 1, "C")
        pdf.cell(
            0,
            5,
            (
                f"Auditor: {self.auditor_name} • "
                f"Powered by DeepSeek AI Vision • © 2026 ThriveAI"
            ),
            0,
            1,
            "C",
        )
        pdf.cell(0, 5, "Confidential • For Internal & Regulatory Use Only", 0, 1, "C")

        # Page number
        pdf.cell(0, 5, f"Page {pdf.page_no()}", 0, 0, "C")
