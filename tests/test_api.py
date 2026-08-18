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


def test_decision_packet_is_single_call_idempotent_and_advisory(tmp_path) -> None:
    client = TestClient(create_app(Settings(environment="test", data_dir=tmp_path, api_key=None)))
    observation = _observation(
        "eccc-geomet",
        SourceTrust.AUTHORITATIVE_PUBLIC,
        AssertionClass.WEATHER,
        MetricName.WIND_SEVERITY,
        0.3,
    )
    payload = {
        "corridor_id": "packet-corridor",
        "observations": [observation.model_dump(mode="json")],
        "graph": {
            "graph_id": "packet-graph",
            "nodes": [
                {
                    "node_id": "source",
                    "name": "Source",
                    "node_type": "data_feed",
                    "criticality": 0.8,
                },
                {
                    "node_id": "dependent",
                    "name": "Dependent",
                    "node_type": "corridor",
                    "criticality": 1.0,
                },
            ],
            "edges": [
                {
                    "source": "source",
                    "target": "dependent",
                    "dependency_strength": 0.9,
                }
            ],
        },
        "failed_nodes": ["source"],
        "objective": {
            "minimum_continuity": 0.7,
            "maximum_shortage_days": 7,
            "maximum_recovery_days": 45,
            "budget": 1000,
            "human_approval_required": True,
        },
        "available_actions": [],
    }
    headers = {"Idempotency-Key": "decision-packet-1"}
    response = client.post("/v1/decision-packets", headers=headers, json=payload)
    assert response.status_code == 200
    packet = response.json()
    assert packet["contract_version"] == "continuityos.decision-packet.v1"
    assert packet["dependency_assessment"]["failed_nodes"] == ["source"]
    assert packet["approval_required"] is True
    assert "does not execute" in packet["human_action_boundary"]
    replay = client.post("/v1/decision-packets", headers=headers, json=payload)
    assert replay.status_code == 200
    assert replay.json() == packet


def test_assess_validation_errors_do_not_hard_500(tmp_path) -> None:
    client = TestClient(create_app(Settings(environment="test", data_dir=tmp_path, api_key=None)))
    response = client.post(
        "/v1/assess",
        json={"corridor_id": "empty", "observations": []},
    )
    assert response.status_code == 422
    assert "at least one observation" in response.json()["detail"]


def test_sovereign_and_simulation_api_endpoints(tmp_path) -> None:
    client = TestClient(create_app(Settings(environment="test", data_dir=tmp_path, api_key=None)))

    # 1. Sovereign Audit
    audit_res = client.post("/v1/sovereign/audit")
    assert audit_res.status_code == 200
    assert audit_res.json()["compliant"] is True

    # 2. Readiness Endpoint
    readiness_res = client.post(
        "/v1/readiness",
        json={
            "theater_id": "theatre-arctic",
            "overall_continuity": 0.96,
            "inventory_reserve_days": 35.0,
            "corridor_state": "open",
        },
    )
    assert readiness_res.status_code == 200
    assert readiness_res.json()["c_rating"] == "C-1_fully_capable"

    # 3. Inventory Simulation Endpoint
    inv_res = client.post(
        "/v1/inventory/simulate",
        json={
            "profile": {
                "resource_id": "fuel-depot",
                "name": "Strategic Fuel",
                "starting_quantity": 50000.0,
                "unit": "MT",
                "normal_consumption_per_day": 1000.0,
                "degraded_consumption_per_day": 1500.0,
                "replenishment_per_day": 1000.0,
                "replenishment_delay_days": 10,
                "minimum_reserve": 10000.0,
                "critical_threshold": 5000.0,
                "warning_threshold": 15000.0,
            },
            "simulation_days": 30,
            "degraded": True,
        },
    )
    assert inv_res.status_code == 200
    assert len(inv_res.json()["daily_log"]) == 30
    assert inv_res.json()["resource_id"] == "fuel-depot"

    # 4. Recovery Lag Modeling Endpoint
    recov_res = client.post(
        "/v1/recovery/model",
        json={
            "profile": {
                "resource_ref": "port/kirkenes",
                "incident_description": "Ice storm",
                "physical_reopening_days": 3,
                "port_backlog_days": 7,
                "carrier_return_days": 10,
                "vessel_repositioning_days": 14,
                "inventory_replenishment_days": 21,
            },
            "days_since_incident": 4,
        },
    )
    assert recov_res.status_code == 200
    assert recov_res.json()["current_phase"] == "T1_physical_reopening"

    # 5. Threat Scan Endpoint
    threat_res = client.post(
        "/v1/threats/scan",
        json={
            "resource_ref": "corridor/arctic-chokepoint",
            "gnss_residuals": [18.0, 22.0, 31.0],
            "clock_drift_ppm": 9.5,
        },
    )
    assert threat_res.status_code == 200
    assert threat_res.json()["gnss_threat"]["is_spoofed"] is True

    # 6. Intelligence Forecast Endpoint
    forecast_res = client.post(
        "/v1/intelligence/forecast",
        json={
            "graph": {
                "graph_id": "test-ai-graph",
                "nodes": [
                    {"node_id": "n1", "name": "N1", "node_type": "supplier", "criticality": 0.8},
                    {"node_id": "n2", "name": "N2", "node_type": "corridor", "criticality": 0.9},
                ],
                "edges": [{"source": "n1", "target": "n2", "dependency_strength": 0.9}],
            },
            "target_node": "n2",
            "observed_degradations": {"n1": 0.8},
        },
    )
    assert forecast_res.status_code == 200
    assert forecast_res.json()["failure_probability"] > 0.50

    # 7. Crypto Merkle Verify Endpoint
    import hashlib

    from continuityos.crypto import MerkleTree

    tree = MerkleTree([hashlib.sha256(f"leaf_{i}".encode()).hexdigest() for i in range(4)])
    proof = tree.generate_inclusion_proof(1)
    mkl_res = client.post("/v1/crypto/merkle-verify", json=proof.model_dump(mode="json"))
    assert mkl_res.status_code == 200
    assert mkl_res.json()["valid"] is True
