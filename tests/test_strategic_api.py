from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from continuityos.config import Settings
from continuityos.domain import AssertionClass, MetricName, Observation, SourceTrust
from continuityos.service import create_app


def test_strategic_stream_ack_and_cooldown_loop(tmp_path, provenance) -> None:
    api_key = "strategic-api-key-012345678901234567890123456789"
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=api_key))
    client = TestClient(app)
    observation = Observation(
        source_id="eccc-geomet",
        source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        assertion_class=AssertionClass.WEATHER,
        metric=MetricName.WIND_SEVERITY,
        value=0.9,
        unit="normalized",
        observed_at=datetime.now(UTC),
        confidence=0.95,
        provenance=provenance,
    )
    payload = {"observations": [observation.model_dump(mode="json")], "alert_threshold": 0.5}
    headers = {"X-Continuity-API-Key": api_key, "Idempotency-Key": "strategic-loop"}

    first = client.post("/v1/strategic/analyze", json=payload, headers=headers)
    replay = client.post("/v1/strategic/analyze", json=payload, headers=headers)
    assert first.status_code == 200
    assert replay.status_code == 200
    report = first.json()
    assert report["source_freshness"][0]["stale"] is False
    assert report["alerts"][0]["delivery_state"] == "ready"
    assert replay.json() == report

    alert_key = report["alerts"][0]["alert_key"]
    acknowledged = client.post(
        f"/v1/strategic/alerts/{alert_key}/ack",
        headers={"X-Continuity-API-Key": api_key},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["acknowledged"] is True

    replay_after_ack = client.post("/v1/strategic/analyze", json=payload, headers=headers)
    assert replay_after_ack.status_code == 200
    assert replay_after_ack.json()["alerts"][0]["delivery_state"] == "acknowledged"

    stream = client.get(
        "/v1/strategic/stream?duration_seconds=1",
        headers={"X-Continuity-API-Key": api_key},
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: strategic" in stream.text
    assert '"delivery_state":"acknowledged"' in stream.text


def test_strategic_operational_routes_require_auth(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key="x" * 32))
    client = TestClient(app)
    assert client.get("/v1/strategic/stream").status_code == 401
    assert client.post("/v1/strategic/alerts/test/ack").status_code == 401
