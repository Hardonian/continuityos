import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from continuityos.analysis import RegressionRequest, RegressionResult
from continuityos.compiler import ContinuityCompiler
from continuityos.crypto import ZKPReserveProof
from continuityos.decision import DecisionPacketRequest
from continuityos.domain import (
    AssertionClass,
    CompiledPlan,
    CorridorAssessment,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.fusion import FusionEngine
from continuityos.graph import DependencyGraph
from continuityos.public_data import PublicSnapshot
from continuityos.service import (
    AssessmentRequest,
    PublicIndicatorRequest,
    PublicSnapshotRequest,
    StrategicAnalysisRequest,
    create_app,
    get_settings,
)
from continuityos.state import IdempotencyConflict
from continuityos.strategic import StrategicAnalysisReport


@pytest.fixture
def app_client():
    settings = get_settings()
    settings.environment = "production"
    settings.outbound_http_enabled = False
    settings.api_key = "test"
    app = create_app(settings)
    with TestClient(app) as client:
        yield client


def test_idempotency_conflict(app_client):
    request_data = {
        "corridor_id": "test-corridor",
        "observations": []
    }
    app_client.app.state.persistent_state.save_idempotent = MagicMock(side_effect=IdempotencyConflict("conflict"))
    response = app_client.post("/v1/assess", json=request_data, headers={"idempotency-key": "conflict-key", "x-continuity-api-key": "test"})
    assert response.status_code == 409


def test_idempotency_invalid_key(app_client):
    response = app_client.post("/v1/assess", json={"corridor_id": "a", "observations": []}, headers={"idempotency-key": "invalid key ", "x-continuity-api-key": "test"})
    assert response.status_code == 400


def test_public_snapshot_fetch_runtime_error(app_client):
    app_client.app.state.public_data.fetch = AsyncMock(side_effect=RuntimeError("timeout"))
    response = app_client.post("/v1/public-data/snapshots", json={"source_id": "test"}, headers={"x-continuity-api-key": "test"})
    assert response.status_code == 503


def test_public_snapshot_fetch_key_error(app_client):
    app_client.app.state.public_data.fetch = AsyncMock(side_effect=KeyError("invalid source"))
    response = app_client.post("/v1/public-data/snapshots", json={"source_id": "test"}, headers={"x-continuity-api-key": "test"})
    assert response.status_code == 422


def test_public_indicators_runtime_error(app_client):
    with patch("continuityos.service.ECCCGeoMetAdapter.fetch", side_effect=RuntimeError("timeout")):
        response = app_client.post("/v1/public-data/indicators", json={"source_id": "eccc-geomet-alerts"}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 503


def test_public_indicators_dfo_missing_dates(app_client):
    response = app_client.post("/v1/public-data/indicators", json={"source_id": "dfo-iwls"}, headers={"x-continuity-api-key": "test"})
    assert response.status_code == 422


def test_public_indicators_invalid_source(app_client):
    response = app_client.post("/v1/public-data/indicators", json={"source_id": "invalid-source"}, headers={"x-continuity-api-key": "test"})
    assert response.status_code == 422


def test_assess_source_policy_error(app_client):
    with patch("continuityos.service.fusion.assess", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/assess", json={"corridor_id": "a", "observations": []}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_regression_value_error(app_client):
    with patch("continuityos.service.run_regression", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/analysis/regression", json={"dataset_id": "a", "features": [], "target": "b"}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_analyze_graph_value_error(app_client):
    with patch("continuityos.service.dependency_engine.analyze", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/graph/analyze", params={"failed_nodes": ["a"]}, json={"graph_id": "a", "nodes": [], "edges": []}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_compile_plan_value_error(app_client):
    with patch("continuityos.service.compiler.compile", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/compile", json={"network": {"id": "a", "nodes": []}, "policy": {"id": "a", "rules": []}}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_decision_packet_value_error(app_client):
    with patch("continuityos.service.build_decision_packet", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/decision-packets", json={"corridor_id": "a", "observations": []}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_strategic_analyze_value_error(app_client):
    with patch("continuityos.service.build_strategic_report", side_effect=ValueError("invalid")):
        response = app_client.post("/v1/strategic/analyze", json={"corridor_id": "a", "snapshots": []}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 422


def test_acknowledge_strategic_alert_invalid(app_client):
    response = app_client.post("/v1/strategic/alerts//ack", headers={"x-continuity-api-key": "test"})
    assert response.status_code == 404
    response = app_client.post("/v1/strategic/alerts/" + "a"*513 + "/ack", headers={"x-continuity-api-key": "test"})
    assert response.status_code == 400


def test_unacknowledge_strategic_alert_invalid(app_client):
    response = app_client.post("/v1/strategic/alerts//unack", headers={"x-continuity-api-key": "test"})
    assert response.status_code == 404
    response = app_client.post("/v1/strategic/alerts/" + "a"*513 + "/unack", headers={"x-continuity-api-key": "test"})
    assert response.status_code == 400


def test_verify_reserve_proof_failed(app_client):
    with patch("continuityos.crypto.ZKPReserveProof.verify", return_value=False):
        response = app_client.post("/v1/crypto/verify-reserve-proof", json={"commitment_hash_hex": "abcd", "policy_minimum": 10, "reserve_amount": 10, "nonce": "1234"}, headers={"x-continuity-api-key": "test"})
        assert response.status_code == 400


def test_request_guard_oversized(app_client):
    response = app_client.post("/livez", headers={"content-length": "999999999"})
    assert response.status_code == 413


def test_request_guard_invalid_content_length(app_client):
    response = app_client.post("/livez", headers={"content-length": "invalid"})
    assert response.status_code == 413


def test_request_guard_exception(app_client):
    app_client.app.add_route("/error", lambda x: 1/0)
    with pytest.raises(ZeroDivisionError):
        app_client.get("/error")
