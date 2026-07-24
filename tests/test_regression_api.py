from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from continuityos.config import Settings
from continuityos.service import create_app
from continuityos.sources.cache import SnapshotCache


def test_regression_endpoint_is_authenticated_and_idempotent(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            data_dir=tmp_path,
            api_key="test-key-012345678901234567890123456789",
        )
    )
    client = TestClient(app)
    payload = {
        "dataset_id": "api-fixture",
        "target_name": "delay_hours",
        "rows": [
            {
                "observed_at": (
                    datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=index)
                ).isoformat(),
                "target": 1.0 + index * 0.5,
                "features": {
                    "sea_ice": float(index),
                    "water_level": float(index % 4),
                },
                "source_ids": ["nsidc-sea-ice-index", "noaa-coops"],
                "snapshot_ids": [f"snapshot-{index}"],
            }
            for index in range(12)
        ],
    }
    assert client.post("/v1/analysis/regression", json=payload).status_code == 401
    headers = {
        "X-Continuity-API-Key": "test-key-012345678901234567890123456789",
        "Idempotency-Key": "regression-fixture",
    }
    first = client.post("/v1/analysis/regression", json=payload, headers=headers)
    second = client.post("/v1/analysis/regression", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert first.json()["test_row_count"] == 3
    assert "source_ids" in first.json()


def test_public_data_routes_are_protected_and_fail_closed_without_outbound(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            data_dir=tmp_path,
            api_key="test-key-012345678901234567890123456789",
            outbound_http_enabled=False,
        )
    )
    client = TestClient(app)
    assert client.get("/v1/public-data/sources").status_code == 401
    headers = {"X-Continuity-API-Key": "test-key-012345678901234567890123456789"}
    listing = client.get("/v1/public-data/sources", headers=headers)
    assert listing.status_code == 200
    assert any(item["source_id"] == "statcan-wds" for item in listing.json())
    blocked = client.post(
        "/v1/public-data/snapshots",
        json={"source_id": "statcan-wds"},
        headers=headers,
    )
    assert blocked.status_code == 503


def test_interoperability_manifest_is_protected_and_truthful(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            data_dir=tmp_path,
            api_key="test-key-012345678901234567890123456789",
            outbound_http_enabled=False,
        )
    )
    client = TestClient(app)
    assert client.get("/v1/interoperability").status_code == 401
    response = client.get(
        "/v1/interoperability",
        headers={"X-Continuity-API-Key": "test-key-012345678901234567890123456789"},
    )
    assert response.status_code == 200
    manifest = response.json()
    assert manifest["claim_boundary"].startswith("This manifest reports implemented")
    capabilities = {item["protocol"]: item for item in manifest["capabilities"]}
    assert capabilities["operator-telemetry-hmac-json"]["status"] == "implemented"
    assert capabilities["ogc-api-features"]["status"] == "source-consumer"
    assert capabilities["common-alerting-protocol"]["status"] == "planned"


def test_cached_eccc_indicators_are_served_without_outbound(tmp_path) -> None:
    cache = SnapshotCache(tmp_path / "public-snapshots")
    body = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-70.0, 47.0]},
                "properties": {
                    "alert_code": "EHW",
                    "alert_type": "warning",
                    "alert_name_en": "heat warning",
                    "publication_datetime": "2026-07-23T00:00:00Z",
                    "expiration_datetime": "2026-07-24T00:00:00Z",
                    "confidence_en": "High",
                    "impact_en": "Moderate",
                    "province": "QC",
                },
            }
        ],
    }
    payload_path = tmp_path / "eccc.json"
    payload_path.write_text(json.dumps(body))
    cache.import_file(
        "eccc-geomet-alerts",
        "https://api.weather.gc.ca/collections/weather-alerts/items?f=json&limit=100",
        payload_path,
    )
    app = create_app(
        Settings(
            environment="test",
            data_dir=tmp_path,
            api_key="test-key-012345678901234567890123456789",
            outbound_http_enabled=False,
        )
    )
    client = TestClient(app)
    response = client.post(
        "/v1/public-data/indicators",
        json={"source_id": "eccc-geomet-alerts"},
        headers={"X-Continuity-API-Key": "test-key-012345678901234567890123456789"},
    )
    assert response.status_code == 200
    assert response.json()["indicators"][0]["indicator_id"] == "eccc.alert.ehw"
