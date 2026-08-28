import struct
from datetime import UTC, datetime

import pytest

from continuityos.edge import IoTMeshNode, ModelPayload
from continuityos.intelligence import DistillationResult, ModelDistiller
from continuityos.telemetry import (
    DroneKinematics,
    TelemetryParser,
    ThreatIndicatorType,
)


def test_iot_mesh_node_registration():
    node = IoTMeshNode("fleet-01")
    node.register_device("esp32-alpha")
    assert "esp32-alpha" in node.devices


def test_iot_mesh_node_deploy_model():
    node = IoTMeshNode("fleet-01")
    payload = ModelPayload(
        model_id="test_q4",
        version="1.0.0",
        layer_embeddings_hex="abcd",
        vocabulary_hex="1234"
    )
    node.deploy_model(payload)
    assert "test_q4" in node.active_deployments


def test_iot_mesh_node_delta_sync():
    node = IoTMeshNode("fleet-01")
    node.register_device("esp32-alpha")

    sync = node.get_delta_sync("esp32-alpha", "last_hash")
    assert sync["type"] == "delta_sync"
    assert sync["base_hash"] == "last_hash"

    with pytest.raises(ValueError, match="Unknown device"):
        node.get_delta_sync("unknown", "hash")


def test_model_distiller():
    distiller = ModelDistiller()
    result = distiller.generate_moe_payload("llama3", "surveillance")

    assert isinstance(result, DistillationResult)
    assert result.compression_ratio == 42.5
    assert result.payload.target_architecture == "esp32-s3"
    assert "llama3" in result.model_id
    assert "surveillance" in result.model_id


def test_telemetry_parser_kinematics():
    # Format (Little Endian):
    # drone_id (8 bytes string)
    # latitude (float32)
    # longitude (float32)
    # altitude_m (float32)
    # velocity_mps (float32)
    # heading_deg (float32)
    # signal_strength_dbm (float32)
    # timestamp (uint32 epoch)
    drone_id = b"UAV-001\x00"
    lat, lon, alt, vel, hdg, sig = 45.0, -75.0, 100.0, 15.0, 90.0, -50.0
    ts = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())

    payload = struct.pack("<8sffffffI", drone_id, lat, lon, alt, vel, hdg, sig, ts)

    parsed = TelemetryParser.parse_binary_kinematics(payload)
    assert parsed.drone_id == "UAV-001"
    assert parsed.latitude == 45.0
    assert parsed.longitude == -75.0
    assert parsed.altitude_m == 100.0
    assert parsed.velocity_mps == 15.0
    assert parsed.heading_deg == 90.0
    assert parsed.signal_strength_dbm == -50.0


def test_telemetry_parser_too_short():
    with pytest.raises(ValueError, match="Payload too short for kinematics"):
        TelemetryParser.parse_binary_kinematics(b"short")


def test_detect_anomalies_rf_jamming():
    stream = [
        DroneKinematics(
            drone_id="UAV-01", latitude=45.0, longitude=-75.0, altitude_m=100.0,
            velocity_mps=15.0, heading_deg=90.0, signal_strength_dbm=-105.0,
            timestamp=datetime.now(UTC)
        )
    ]
    threats = TelemetryParser.detect_anomalies(stream)
    assert len(threats) == 1
    assert threats[0].indicator_type == ThreatIndicatorType.RF_JAMMING


def test_detect_anomalies_gps_spoofing():
    stream = [
        DroneKinematics(
            drone_id="UAV-01", latitude=45.0, longitude=-75.0, altitude_m=100.0,
            velocity_mps=400.0, heading_deg=90.0, signal_strength_dbm=-50.0,
            timestamp=datetime.now(UTC)
        )
    ]
    threats = TelemetryParser.detect_anomalies(stream)
    assert len(threats) == 1
    assert threats[0].indicator_type == ThreatIndicatorType.GPS_SPOOFING


def test_detect_anomalies_empty():
    threats = TelemetryParser.detect_anomalies([])
    assert len(threats) == 0

import asyncio
from unittest.mock import MagicMock, patch

from continuityos.edge import EdgeNode


def test_edge_node_add_peer():
    node = EdgeNode("node1", MagicMock())
    node.add_peer("http://peer1/")
    assert "http://peer1" in node.peers

def test_edge_node_get_manifest(tmp_path):
    cache_mock = MagicMock()
    cache_mock.root = tmp_path

    # Create fake metadata.json
    d = tmp_path / "a" / "b" / "c"
    d.mkdir(parents=True)
    (d / "metadata.json").write_text('{"snapshot_id": "snap1"}')

    node = EdgeNode("node1", cache_mock)
    manifest = node.get_manifest()
    assert manifest.peer_id == "node1"
    assert "snap1" in manifest.snapshot_ids

@pytest.mark.anyio
async def test_edge_node_sync_with_peer_success():
    cache_mock = MagicMock()
    node = EdgeNode("node1", cache_mock)

    mock_response_manifest = MagicMock()
    mock_response_manifest.status_code = 200
    mock_response_manifest.json.return_value = {"peer_id": "peer1", "snapshot_ids": ["snap1"]}

    mock_response_sync = MagicMock()
    mock_response_sync.status_code = 200
    mock_response_sync.json.return_value = {
        "metadata": {"source_id": "src1", "url": "url1", "content_type": "text/plain"},
        "payload": "payload_data"
    }

    async def mock_get(url):
        if url.endswith("/manifest"):
            return mock_response_manifest
        return mock_response_sync

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        await node._sync_with_peer("http://peer1")
        cache_mock.store.assert_called_once()

@pytest.mark.anyio
async def test_edge_node_loop_start_stop():
    node = EdgeNode("node1", MagicMock(), gossip_interval=0.01)
    node.start()
    assert node._running is True
    assert node._task is not None
    await asyncio.sleep(0.02)
    await node.stop()
    assert node._running is False
    assert node._task is None

@pytest.mark.anyio
async def test_edge_node_sync_manifest_error():
    cache_mock = MagicMock()
    node = EdgeNode("node1", cache_mock)

    mock_response = MagicMock()
    mock_response.status_code = 500

    async def mock_get(url):
        return mock_response

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        await node._sync_with_peer("http://peer1")
        # should return without storing

@pytest.mark.anyio
async def test_edge_node_sync_request_error():
    import httpx
    cache_mock = MagicMock()
    node = EdgeNode("node1", cache_mock)

    with patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("err")):
        await node._sync_with_peer("http://peer1")
        # should catch error and continue

def test_edge_node_get_manifest_invalid_json(tmp_path):
    cache_mock = MagicMock()
    cache_mock.root = tmp_path
    d = tmp_path / "a" / "b" / "c"
    d.mkdir(parents=True)
    (d / "metadata.json").write_text('{invalid_json}')
    node = EdgeNode("node1", cache_mock)
    manifest = node.get_manifest()
    assert len(manifest.snapshot_ids) == 0

from continuityos.domain import (
    AssertionClass,
    CorridorAssessment,
    CorridorState,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.graph import DependencyGraph, DependencyNode, NodeType
from continuityos.intelligence import (
    BayesianCascadeForecaster,
    TelemetryAnomalyForecaster,
    XAIRiskExplainer,
)


def test_bayesian_cascade_forecaster():
    forecaster = BayesianCascadeForecaster()
    graph = DependencyGraph(
        graph_id="a",
        nodes=[DependencyNode(node_id="n1", name="n1", node_type=NodeType.PORT, criticality=0.8), DependencyNode(node_id="n2", name="n2", node_type=NodeType.PORT, criticality=0.5)],
        edges=[]
    )
    res = forecaster.forecast(graph, "n2", {"n1": 0.5})
    assert res.target_node_id == "n2"

def test_telemetry_anomaly_forecaster():
    forecaster = TelemetryAnomalyForecaster()
    Observation(
        source_id="s1",
        source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
        assertion_class=AssertionClass.LIVE_CAPACITY,
        metric=MetricName.PORT_CAPACITY,
        value=0.9,
        unit="test",
        observed_at=datetime.now(UTC),
        confidence=1.0,
        provenance=Provenance(uri="mock://test", content_sha256="0" * 64),
        metadata={}
    )
    res = forecaster.analyze_stream("metric1", [0.8, 0.85, 0.9], 0.9)
    assert res.metric_name == "metric1"

def test_explainable_ai_attribution():
    explainer = XAIRiskExplainer()
    DependencyGraph(graph_id="a", nodes=[], edges=[])
    assessment = CorridorAssessment(
        corridor_id="a",
        generated_at=datetime.now(UTC),
        overall_risk=0.5,
        confidence=0.5,
        state=CorridorState.OPEN,
        factors=[],
        missing_required_metrics=[],
        caveats=[]
    )
    exp = explainer.explain(assessment)
    assert exp is not None
