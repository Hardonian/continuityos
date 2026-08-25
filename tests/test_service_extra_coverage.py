"""Targeted REST API endpoint unit tests for service.py coverage boost.

Targets: service.py coverage from 87% → ≥95%.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from continuityos.config import Settings
from continuityos.public_data import NormalizedIndicator, PublicSnapshot
from continuityos.service import create_app


@pytest.fixture
def auth_client(tmp_path: Path) -> tuple[TestClient, dict[str, str]]:
    api_key = "test-api-key-012345678901234567890123456789"
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=api_key))
    client = TestClient(app)
    headers = {"X-Continuity-API-Key": api_key}
    return client, headers


def test_strategic_alert_ack_unack_flow(auth_client: tuple[TestClient, dict[str, str]]) -> None:
    """Test acknowledging and unacknowledging a strategic alert."""
    client, headers = auth_client

    # First ack
    resp_ack = client.post("/v1/strategic/alerts/ALERT-ARCTIC-ICE/ack", headers=headers)
    assert resp_ack.status_code == 200
    data_ack = resp_ack.json()
    assert data_ack["alert_key"] == "ALERT-ARCTIC-ICE"
    assert data_ack["acknowledged"] is True

    # Then unack
    resp_unack = client.post("/v1/strategic/alerts/ALERT-ARCTIC-ICE/unack", headers=headers)
    assert resp_unack.status_code == 200
    data_unack = resp_unack.json()
    assert data_unack["alert_key"] == "ALERT-ARCTIC-ICE"
    assert data_unack["acknowledged"] is False


def test_strategic_alert_invalid_keys(auth_client: tuple[TestClient, dict[str, str]]) -> None:
    """Test validation errors for invalid alert keys."""
    client, headers = auth_client

    # Too long alert key
    huge_key = "A" * 600
    resp = client.post(f"/v1/strategic/alerts/{huge_key}/ack", headers=headers)
    assert resp.status_code == 400

    resp_unack = client.post(f"/v1/strategic/alerts/{huge_key}/unack", headers=headers)
    assert resp_unack.status_code == 400


def test_public_indicators_endpoint_cdd(auth_client: tuple[TestClient, dict[str, str]]) -> None:
    """Test /v1/public-data/indicators for Canadian Disaster Database adapter."""
    client, headers = auth_client

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
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "canadian-disaster-database"
        assert len(data["indicators"]) == 1


def test_public_indicators_endpoint_dfo(auth_client: tuple[TestClient, dict[str, str]]) -> None:
    """Test /v1/public-data/indicators for DFO IWLS adapter."""
    client, headers = auth_client

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
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "dfo-iwls"
        assert len(data["indicators"]) == 1


def test_public_indicators_dfo_missing_dates(
    auth_client: tuple[TestClient, dict[str, str]],
) -> None:
    """DFO indicators request missing start/end dates returns 422/400."""
    client, headers = auth_client
    resp = client.post(
        "/v1/public-data/indicators",
        json={"source_id": "dfo-iwls", "region": "ATL"},
        headers=headers,
    )
    assert resp.status_code in {400, 422}


def test_public_indicators_unimplemented_source(
    auth_client: tuple[TestClient, dict[str, str]],
) -> None:
    """Source without indicator adapter returns 422/400."""
    client, headers = auth_client
    resp = client.post(
        "/v1/public-data/indicators",
        json={"source_id": "statcan-wds"},
        headers=headers,
    )
    assert resp.status_code in {400, 422}


def test_wargame_simulate_fallback_scenario(
    auth_client: tuple[TestClient, dict[str, str]],
) -> None:
    """Wargame simulation falls back to default scenario on invalid string."""
    client, headers = auth_client
    resp = client.post(
        "/v1/wargame/simulate",
        json={"scenario_type": "invalid_unknown_scenario"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "scenario_type" in data


def test_rbac_evaluate_role_fallback(auth_client: tuple[TestClient, dict[str, str]]) -> None:
    """RBAC evaluate endpoint falls back to operator_analyst on invalid role string."""
    client, headers = auth_client
    resp = client.post(
        "/v1/rbac/evaluate",
        json={
            "user_id": "USER-01",
            "roles": ["invalid_custom_role"],
            "clearance_level": "INVALID_LEVEL",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "is_authorized" in data


def test_database_evidence_query_endpoint(
    auth_client: tuple[TestClient, dict[str, str]],
) -> None:
    """Test /v1/database/evidence/query endpoint."""
    client, headers = auth_client
    resp = client.get(
        "/v1/database/evidence/query",
        params={"tenant_id": "DND-CARLING-HQ", "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_count" in data
    assert "records" in data
