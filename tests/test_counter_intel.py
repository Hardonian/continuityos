"""Test suite for Counter-Intelligence, Dark Fleet, and Anti-Reconnaissance engines."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.counter_intel import (
    DarkFleetDetector,
    EMCONLevel,
    InsiderReconDetector,
    SARSatelliteOverflightPredictor,
)
from continuityos.domain import GeoPoint
from continuityos.service import create_app


class TestDarkFleetDetector:
    """Test correlation of radar contacts vs AIS transponders."""

    def test_dark_vessel_detection_nominal(self) -> None:
        detector = DarkFleetDetector()
        contacts = [
            {"latitude": 48.1, "longitude": -65.0, "speed_knots": 12.0, "mmsi": "316001234"},
            {"latitude": 48.2, "longitude": -65.1, "speed_knots": 1.5, "mmsi": None},  # Dark
        ]
        active_mmsis = {"316001234"}
        assessment = detector.correlate_contacts(
            corridor_id="TEST-GULF",
            radar_optical_contacts=contacts,
            active_ais_mmsis=active_mmsis,
            asset_location=GeoPoint(latitude=48.0, longitude=65.0),
        )

        assert assessment.total_contacts_detected == 2
        assert assessment.dark_vessels_count == 1
        assert assessment.highest_threat_score > 0.4


class TestSARSatelliteOverflightPredictor:
    """Test orbital SAR and Earth Observation reconnaissance pass prediction."""

    def test_sar_overflight_evaluation(self) -> None:
        predictor = SARSatelliteOverflightPredictor()
        ephemeris = [
            {"satellite_id": "COSMO-4", "sensor_type": "SAR_RADAR", "elevation_max_deg": 75.0},
            {"satellite_id": "OPT-1", "sensor_type": "OPTICAL_HIGH_RES", "elevation_max_deg": 30.0},
        ]
        report = predictor.evaluate_exposure(
            corridor_id="ARCTIC-CONVOY-01",
            orbital_ephemeris=ephemeris,
        )

        assert report.total_passes_projected == 2
        assert report.peak_vulnerability_index > 0.7
        assert report.recommended_emcon_level in {
            EMCONLevel.ALPHA_SILENT,
            EMCONLevel.BRAVO_LOW_PROBABILITY,
        }


class TestInsiderReconDetector:
    """Test telemetry scraping and counter-intelligence reconnaissance detection."""

    def test_insider_recon_anomaly(self) -> None:
        detector = InsiderReconDetector()
        res = detector.evaluate_query_telemetry(
            operator_id="OP-SUSPECT-01",
            query_count_last_hour=800,
            geographic_bounding_boxes_scraped=35,
            attempted_clearance_escalations=2,
        )

        assert res["is_anomaly_threat"] is True
        assert res["counter_intel_threat_score"] > 0.7
        assert len(res["anomaly_flags"]) >= 3


class TestCounterIntelAPI:
    """Test counter-intel REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_assess_counter_surveillance_endpoint(self, client: TestClient) -> None:
        payload = {
            "corridor_id": "TEST-CORRIDOR",
            "orbital_ephemeris": [
                {"satellite_id": "SAR-01", "sensor_type": "SAR_RADAR", "elevation_max_deg": 65.0}
            ],
            "corridor_length_km": 120.0,
        }
        resp = client.post("/v1/intel/counter-surveillance/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_passes_projected"] == 1
        assert "recommended_emcon_level" in data

    def test_correlate_dark_fleet_endpoint(self, client: TestClient) -> None:
        payload = {
            "corridor_id": "CHOKEPOINT-01",
            "contacts": [{"latitude": 48.5, "longitude": -64.2, "speed_knots": 1.2, "mmsi": None}],
            "active_mmsis": [],
            "asset_latitude": 48.4,
            "asset_longitude": -64.0,
        }
        resp = client.post("/v1/intel/dark-fleet/correlate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["dark_vessels_count"] == 1
