"""Tests for Progress Tracker AI – Milestone verification."""

import pytest

from core.progress_tracker_ai import (
    ProgressTrackerAI,
)


@pytest.fixture
def tracker():
    return ProgressTrackerAI()


class TestProgressTrackerAI:
    def test_no_findings_zero_progress(self, tracker):
        report = tracker.analyze_progress("100")
        assert report.overall_pct_complete == 0.0
        assert len(report.milestones) > 0

    def test_excavation_milestone(self, tracker):
        findings = [
            {"milestone": "EXCAVATION", "confidence": 1.0},
        ]
        report = tracker.analyze_progress("100", image_findings=findings)
        exc = next(m for m in report.milestones if m.milestone_key == "EXCAVATION")
        assert exc.actual_pct == 100.0
        assert exc.verified is True

    def test_schedule_variance(self, tracker):
        findings = [
            {"milestone": "EXCAVATION", "confidence": 1.0},
        ]
        scheduled = {"EXCAVATION": 100.0, "SUPERSTRUCTURE": 50.0}
        report = tracker.analyze_progress(
            "100", image_findings=findings, scheduled=scheduled
        )
        # Excavation is on track, superstructure behind
        super_m = next(
            m for m in report.milestones if m.milestone_key == "SUPERSTRUCTURE"
        )
        assert super_m.variance < 0

    def test_change_orders_stored(self, tracker):
        co = [{"id": "CO-1", "amount": 15000, "reason": "Unforeseen rock"}]
        report = tracker.analyze_progress("100", change_orders=co)
        assert len(report.change_orders) == 1
        assert report.change_orders[0]["id"] == "CO-1"

    def test_lien_waiver_milestones(self, tracker):
        findings = [
            {"milestone": "EXCAVATION", "confidence": 1.0},
        ]
        report = tracker.analyze_progress("100", image_findings=findings)
        assert "Foundation & Earthwork" in report.lien_waiver_milestones

    def test_summary_generated(self, tracker):
        findings = [
            {"milestone": "EXCAVATION", "confidence": 1.0},
            {"milestone": "SUPERSTRUCTURE", "confidence": 0.3},
        ]
        report = tracker.analyze_progress("100", image_findings=findings)
        assert "complete" in report.summary.lower()

    def test_get_reports_filtered(self, tracker):
        tracker.analyze_progress("100")
        tracker.analyze_progress("200")
        assert len(tracker.get_reports("100")) == 1
        assert len(tracker.get_reports()) == 2
