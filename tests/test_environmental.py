"""Test suite for Geographic, Environmental, Permafrost, and Subsea models."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.environmental import (
    PermafrostDegradationModel,
    SubseaAcousticMonitor,
    TrackStabilityStatus,
    WildfireCorridorRiskModel,
)
from continuityos.service import create_app


class TestPermafrostDegradationModel:
    """Test active-layer thaw and track settlement simulation."""

    def test_permafrost_thaw_moderate(self) -> None:
        model = PermafrostDegradationModel()
        report = model.evaluate_corridor_thaw(
            corridor_id="HUDSON-BAY-TEST",
            degree_days_of_thaw=400.0,
            insulating_peat_cover_cm=15.0,
        )

        assert report.calculated_thaw_depth_cm > 0
        assert report.stability_status in {
            TrackStabilityStatus.STABLE_FULL_SPEED,
            TrackStabilityStatus.SPEED_RESTRICTED,
        }
        assert report.recommended_max_speed_mph in {15, 45}

    def test_permafrost_thaw_severe(self) -> None:
        model = PermafrostDegradationModel()
        report = model.evaluate_corridor_thaw(
            corridor_id="HUDSON-BAY-SEVERE",
            degree_days_of_thaw=1200.0,
            insulating_peat_cover_cm=2.0,
        )

        assert report.calculated_thaw_depth_cm > 80.0
        assert report.stability_status == TrackStabilityStatus.CRITICAL_SETTLEMENT_SUSPENSION
        assert report.recommended_max_speed_mph == 0


class TestWildfireCorridorRiskModel:
    """Test Canadian Fire Weather Index and flame proximity projection."""

    def test_wildfire_high_risk(self) -> None:
        model = WildfireCorridorRiskModel()
        report = model.evaluate_wildfire_risk(
            corridor_id="FRASER-CANYON",
            fwi=38.0,
            closest_fire_distance_km=5.0,
            wind_speed_kmh=35.0,
            wind_direction_towards_corridor=True,
        )

        assert report.corridor_closure_probability > 0.6
        assert report.visibility_reduction_percent > 50.0
        assert "CRITICAL" in report.operational_recommendation


class TestSubseaAcousticMonitor:
    """Test subsea cable integrity and anchor-drag acoustic monitoring."""

    def test_subsea_anchor_hazard(self) -> None:
        monitor = SubseaAcousticMonitor()
        report = monitor.evaluate_subsea_risk(
            infrastructure_id="HALIFAX-FIBER-01",
            acoustic_anomaly_db=22.0,
            closest_anchoring_vessel_dist_km=1.8,
        )

        assert report.acoustic_anomaly_level > 0.6
        assert report.integrity_score < 0.5
        assert report.choke_point_status == "HIGH_THREAT_ANOMALY"


class TestEnvironmentalAPI:
    """Test environmental REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_permafrost_endpoint(self, client: TestClient) -> None:
        payload = {
            "corridor_id": "TEST-PERMAFROST",
            "degree_days_of_thaw": 500.0,
            "insulating_peat_cover_cm": 10.0,
        }
        resp = client.post("/v1/environmental/permafrost-assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "calculated_thaw_depth_cm" in data

    def test_wildfire_endpoint(self, client: TestClient) -> None:
        payload = {
            "corridor_id": "TEST-WILDFIRE",
            "fire_weather_index_fwi": 30.0,
            "closest_fire_distance_km": 10.0,
        }
        resp = client.post("/v1/environmental/wildfire-corridor-risk", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "corridor_closure_probability" in data

    def test_subsea_endpoint(self, client: TestClient) -> None:
        payload = {
            "infrastructure_id": "TEST-SUBSEA",
            "acoustic_anomaly_db": 10.0,
            "closest_anchoring_vessel_dist_km": 5.0,
        }
        resp = client.post("/v1/environmental/subsea-integrity", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "integrity_score" in data
