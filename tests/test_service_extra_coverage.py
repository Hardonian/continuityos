"""Targeted REST API endpoint unit tests for service.py coverage boost.

Targets: service.py coverage from 87% → ≥95%.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from continuityos.public_data import NormalizedIndicator, PublicSnapshot
from continuityos.service import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_strategic_alert_ack_unack_flow(client: TestClient) -> None:
    """Test acknowledging and unacknowledging a strategic alert."""
    # First ack
    resp_ack = client.post("/v1/strategic/alerts/ALERT-ARCTIC-ICE/ack")
    assert resp_ack.status_code == 200
    data_ack = resp_ack.json()
    assert data_ack["alert_key"] == "ALERT-ARCTIC-ICE"
    assert data_ack["acknowledged"] is True

    # Then unack
    resp_unack = client.post("/v1/strategic/alerts/ALERT-ARCTIC-ICE/unack")
    assert resp_unack.status_code == 200
    data_unack = resp_unack.json()
    assert data_unack["alert_key"] == "ALERT-ARCTIC-ICE"
    assert data_unack["acknowledged"] is False


def test_strategic_alert_invalid_keys(client: TestClient) -> None:
    """Test validation errors for invalid alert keys."""
    # Too long alert key
    huge_key = "A" * 600
    resp = client.post(f"/v1/strategic/alerts/{huge_key}/ack")
    assert resp.status_code == 400

    resp_unack = client.post(f"/v1/strategic/alerts/{huge_key}/unack")
    assert resp_unack.status_code == 400


def test_public_indicators_endpoint_cdd(client: TestClient) -> None:
    """Test /v1/public-data/indicators for Canadian Disaster Database adapter."""
    mock_snapshot = PublicSnapshot(
        source_id="canadian-disaster-database",
        snapshot_id="snap-cdd-1",
        content_sha256="a" * 64,
        retrieved_at=datetime.now(UTC),
        status_code=200,
        parser="xlsx",
        record_count=1,
        freshness_hours=720.0,
        quality_flags=(),
    )
    mock_indicators = [
        NormalizedIndicator(
            indicator_id="cdd.disaster_event",
            observed_at=datetime(2024, 1, 1, tzinfo=UTC),
            value=1.0,
            unit="event",
            source_id="canadian-disaster-database",
            provenance_snapshot_ids=("snap-cdd-1",),
            quality_flags=(),
            metadata={"event_id": "EVT-1"},
        )
    ]

    with patch(
        "continuityos.public_data.CanadianDisasterDatabaseAdapter.fetch",
        new=AsyncMock(return_value=(mock_snapshot, mock_indicators)),
    ):
        resp = client.post(
            "/v1/public-data/indicators",
            json={"source_id": "canadian-disaster-database", "force": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "canadian-disaster-database"
        assert len(data["indicators"]) == 1


def test_public_indicators_endpoint_dfo(client: TestClient) -> None:
    """Test /v1/public-data/indicators for DFO IWLS adapter."""
    mock_stn_snap = PublicSnapshot(
        source_id="dfo-iwls",
        snapshot_id="snap-dfo-stn",
        content_sha256="b" * 64,
        retrieved_at=datetime.now(UTC),
        status_code=200,
        parser="json",
        record_count=1,
        freshness_hours=1.0,
        quality_flags=(),
    )
    mock_data_snap = PublicSnapshot(
        source_id="dfo-iwls",
        snapshot_id="snap-dfo-data",
        content_sha256="c" * 64,
        retrieved_at=datetime.now(UTC),
        status_code=200,
        parser="json",
        record_count=1,
        freshness_hours=1.0,
        quality_flags=(),
    )
    mock_indicators = [
        NormalizedIndicator(
            indicator_id="dfo.water_level",
            observed_at=datetime(2024, 1, 1, tzinfo=UTC),
            value=1.45,
            unit="metres",
            source_id="dfo-iwls",
            provenance_snapshot_ids=("snap-dfo-stn", "snap-dfo-data"),
            quality_flags=(),
            metadata={"station_code": "HLX"},
        )
    ]

    with patch(
        "continuityos.public_data.DFOIWLSAdapter.fetch_current",
        new=AsyncMock(
            return_value=(mock_stn_snap, mock_data_snap, {"id": "STN-1"}, mock_indicators)
        ),
    ):
        resp = client.post(
            "/v1/public-data/indicators",
            json={
                "source_id": "dfo-iwls",
                "region": "ATL",
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z",
                "force": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "dfo-iwls"
        assert len(data["indicators"]) == 1


def test_public_indicators_dfo_missing_dates(client: TestClient) -> None:
    """DFO indicators request missing start/end dates returns 422/400."""
    resp = client.post(
        "/v1/public-data/indicators",
        json={"source_id": "dfo-iwls", "region": "ATL"},
    )
    assert resp.status_code in {400, 422}


def test_public_indicators_unimplemented_source(client: TestClient) -> None:
    """Source without indicator adapter returns 422/400."""
    resp = client.post(
        "/v1/public-data/indicators",
        json={"source_id": "statcan-wds"},
    )
    assert resp.status_code in {400, 422}


def test_threat_telemetry_scan_endpoint(client: TestClient) -> None:
    """Test /v1/threat/telemetry/scan endpoint with synthetic radar & AIS inputs."""
    payload: dict[str, Any] = {
        "corridor_id": "CORR-HALIFAX",
        "radar_optical_contacts": [
            {
                "contact_id": "RADAR-001",
                "latitude": 44.65,
                "longitude": -63.58,
                "speed_knots": 14.5,
                "heading_deg": 180.0,
                "detected_at": "2024-01-15T12:00:00Z",
            }
        ],
        "ais_broadcasts": [
            {
                "mmsi": 999999999,
                "latitude": 44.65,
                "longitude": -63.58,
                "speed_knots": 14.5,
                "heading_deg": 180.0,
                "timestamp": "2024-01-15T12:00:00Z",
            }
        ],
    }
    resp = client.post("/v1/threat/telemetry/scan", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "findings" in data or "contacts_correlated" in data or "threat_score" in data
