from __future__ import annotations

from fastapi.testclient import TestClient

from continuityos.config import Settings
from continuityos.service import create_app


def test_production_protected_routes_require_api_key(tmp_path) -> None:
    settings = Settings(environment="test", data_dir=tmp_path, api_key="a" * 32)
    client = TestClient(create_app(settings))
    assert client.get("/healthz").status_code == 200
    assert client.get("/v1/evidence/verify").status_code == 401
    assert (
        client.get("/v1/evidence/verify", headers={"X-Continuity-API-Key": "wrong"}).status_code
        == 401
    )
    assert (
        client.get("/v1/evidence/verify", headers={"X-Continuity-API-Key": "a" * 32}).status_code
        == 200
    )


def test_request_id_metrics_and_protected_pagination(tmp_path) -> None:
    settings = Settings(
        environment="test", data_dir=tmp_path, api_key=None, rate_limit_per_minute=2
    )
    client = TestClient(create_app(settings))
    response = client.get("/healthz", headers={"X-Request-ID": "test-request"})
    assert response.headers["X-Request-ID"] == "test-request"
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "continuityos_requests_total" in metrics.text
    assert client.get("/v1/evidence?offset=0&limit=1").status_code == 200


def test_protected_rate_limit_returns_retry_after(tmp_path) -> None:
    settings = Settings(
        environment="test", data_dir=tmp_path, api_key="a" * 32, rate_limit_per_minute=1
    )
    client = TestClient(create_app(settings))
    headers = {"X-Continuity-API-Key": "a" * 32}
    assert client.get("/v1/evidence/verify", headers=headers).status_code == 200
    limited = client.get("/v1/evidence/verify", headers=headers)
    assert limited.status_code == 429
    assert limited.headers["Retry-After"].isdigit()
