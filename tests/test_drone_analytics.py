"""Tests for Drone Analytics Bridge – Aerial intelligence."""

import pytest

from core.drone_analytics_bridge import (
    DroneAnalyticsBridge,
)


@pytest.fixture
def drone():
    return DroneAnalyticsBridge()


class TestDroneAnalyticsBridge:
    def test_ingest_captures(self, drone):
        raw = [
            {"area_acres": 1.5, "altitude_ft": 200, "image_count": 100},
            {"area_acres": 0.5, "altitude_ft": 150, "image_count": 50},
        ]
        captures = drone.ingest_captures("100", raw)
        assert len(captures) == 2
        assert captures[0].area_acres == 1.5
        assert captures[1].image_count == 50

    def test_estimate_volumes_excavation(self, drone):
        findings = [
            {"name": "excavation area", "volume_cy": 2340, "confidence": 0.90},
        ]
        volumes = drone.estimate_volumes(findings)
        assert len(volumes) == 1
        assert volumes[0].material == "excavation"
        assert volumes[0].volume_cy == 2340

    def test_estimate_volumes_concrete(self, drone):
        findings = [
            {"name": "concrete pour", "volume_cy": 500, "confidence": 0.85},
        ]
        volumes = drone.estimate_volumes(findings)
        assert len(volumes) == 1
        assert volumes[0].material == "concrete"

    def test_estimate_no_volumes(self, drone):
        findings = [
            {"name": "worker on site", "confidence": 0.9},
        ]
        volumes = drone.estimate_volumes(findings)
        assert len(volumes) == 0

    def test_full_analysis(self, drone):
        captures = [
            {"area_acres": 2.0, "altitude_ft": 250, "image_count": 200},
        ]
        findings = [
            {"name": "excavation complete", "volume_cy": 2340, "confidence": 0.90},
        ]
        timeline = [
            {
                "date": "2026-01-15T10:00:00",
                "milestone": "EXCAVATION",
                "progress_pct": 87,
            },
        ]
        result = drone.analyze("100", captures, findings, timeline)
        assert result.total_area_acres == 2.0
        assert result.total_images == 200
        assert len(result.volumes) == 1
        assert result.site_progress_pct == 87.0
        assert "2,340 CY" in result.summary

    def test_processing_time_estimate(self, drone):
        captures = [{"area_acres": 1.0, "image_count": 50}]
        result = drone.analyze("100", captures)
        # Should be < 5 min (300s) per acre
        assert result.processing_time_sec <= 300.0

    def test_empty_analysis(self, drone):
        result = drone.analyze("100")
        assert result.total_area_acres == 0.0
        assert result.total_images == 0

    def test_get_results_filtered(self, drone):
        drone.analyze("100")
        drone.analyze("200")
        assert len(drone.get_results("100")) == 1
        assert len(drone.get_results()) == 2
