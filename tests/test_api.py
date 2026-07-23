from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from continuityos.config import Settings
from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.service import create_app


def _provenance() -> Provenance:
    return Provenance(
        uri="fixture://api",
        content_sha256=hashlib.sha256(b"api").hexdigest(),
        licence="test",
    )


def _observation(
    source_id: str,
    trust: SourceTrust,
    assertion: AssertionClass,
    metric: MetricName,
    value: float,
) -> Observation:
    return Observation(
        source_id=source_id,
        source_trust=trust,
        assertion_class=assertion,
        metric=metric,
        value=value,
        unit="days" if metric == MetricName.INVENTORY_DAYS else "ratio",
        observed_at=datetime.now(UTC),
        confidence=0.95,
        provenance=_provenance(),
    )


def test_health_sources_assessment_graph_compile_and_evidence(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=None))
    client = TestClient(app)
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert client.get("/livez").json() == {"status": "ok"}
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    sources = client.get("/v1/sources")
    assert sources.status_code == 200
    ids = {item["source_id"] for item in sources.json()}
    assert {"nsidc-sea-ice-index", "operator-telemetry"}.issubset(ids)

    observations = [
        _observation(
            "eccc-geomet",
            SourceTrust.AUTHORITATIVE_PUBLIC,
            AssertionClass.ICE,
            MetricName.SEA_ICE_CONCENTRATION,
            0.6,
        ),
        _observation(
            "eccc-geomet",
            SourceTrust.AUTHORITATIVE_PUBLIC,
            AssertionClass.WEATHER,
            MetricName.WIND_SEVERITY,
            0.3,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.LIVE_AVAILABILITY,
            MetricName.PORT_AVAILABILITY,
            0.7,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.LIVE_AVAILABILITY,
            MetricName.SATCOM_AVAILABILITY,
            0.7,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.CYBER_HEALTH,
            MetricName.CYBER_CONTROL_HEALTH,
            0.6,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.CYBER_HEALTH,
            MetricName.DATA_INTEGRITY,
            0.8,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.INSURANCE_ACCESS,
            MetricName.INSURANCE_AVAILABILITY,
            0.7,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.LIVE_CAPACITY,
            MetricName.ESCORT_CAPACITY,
            0.5,
        ),
        _observation(
            "operator-telemetry",
            SourceTrust.AUTHENTICATED_OPERATOR,
            AssertionClass.LIVE_CAPACITY,
            MetricName.INVENTORY_DAYS,
            20,
        ),
    ]
    response = client.post(
        "/v1/assess",
        headers={"Idempotency-Key": "assessment-request-1"},
        json={
            "corridor_id": "api-corridor",
            "observations": [item.model_dump(mode="json") for item in observations],
        },
    )
    assert response.status_code == 200
    assessment = response.json()
    replay = client.post(
        "/v1/assess",
        headers={"Idempotency-Key": "assessment-request-1"},
        json={
            "corridor_id": "api-corridor",
            "observations": [item.model_dump(mode="json") for item in observations],
        },
    )
    assert replay.status_code == 200
    assert replay.json() == assessment
    conflict = client.post(
        "/v1/assess",
        headers={"Idempotency-Key": "assessment-request-1"},
        json={
            "corridor_id": "different",
            "observations": [observations[0].model_dump(mode="json")],
        },
    )
    assert conflict.status_code == 409

    graph_response = client.post(
        "/v1/graph/analyze?failed_nodes=idp",
        json={
            "graph_id": "g1",
            "nodes": [
                {
                    "node_id": "idp",
                    "name": "IdP",
                    "node_type": "identity_provider",
                    "criticality": 0.8,
                },
                {
                    "node_id": "port",
                    "name": "Port",
                    "node_type": "port",
                    "criticality": 1.0,
                },
            ],
            "edges": [
                {
                    "source": "idp",
                    "target": "port",
                    "dependency_strength": 0.9,
                }
            ],
        },
    )
    assert graph_response.status_code == 200
    assert graph_response.json()["failed_nodes"] == ["idp"]

    compile_response = client.post(
        "/v1/compile",
        json={
            "assessment": assessment,
            "objective": {
                "minimum_continuity": 0.7,
                "maximum_shortage_days": 7,
                "maximum_recovery_days": 45,
                "budget": 1000,
                "human_approval_required": True,
            },
            "available_actions": [
                {
                    "action_id": "a",
                    "name": "Secondary communications",
                    "cost": 100,
                    "continuity_gain": 0.4,
                    "risk_reductions": {"communications": 0.5},
                    "rationale": "test",
                }
            ],
        },
    )
    assert compile_response.status_code == 200

    evidence = client.get("/v1/evidence")
    assert evidence.status_code == 200
    assert len(evidence.json()) == 3
    verification = client.get("/v1/evidence/verify")
    assert verification.json()["valid"] is True


def test_assess_validation_errors_do_not_hard_500(tmp_path) -> None:
    client = TestClient(create_app(Settings(environment="test", data_dir=tmp_path, api_key=None)))
    response = client.post(
        "/v1/assess",
        json={"corridor_id": "empty", "observations": []},
    )
    assert response.status_code == 422
    assert "at least one observation" in response.json()["detail"]
