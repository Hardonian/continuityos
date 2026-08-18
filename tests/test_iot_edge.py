from datetime import UTC, datetime
import struct

import pytest

from continuityos.edge import IoTMeshNode, ModelPayload
from continuityos.intelligence import ModelDistiller, DistillationResult
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
