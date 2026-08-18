from __future__ import annotations

from fastapi.testclient import TestClient

from continuityos.config import Settings
from continuityos.embedded import CompactBinaryProtocolCodec
from continuityos.service import create_app


def test_tactical_endpoints(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=None))
    client = TestClient(app)

    # 1. UAV analyze
    uav_payload = {
        "drone_id": "UAV-ALPHA-01",
        "latitude": 70.1,
        "longitude": 35.2,
        "altitude_m_msl": 300.0,
        "ground_speed_mps": 22.0,
        "battery_state_of_charge": 0.90,
        "rf_link_margin_db": 24.0,
        "optical_flow_quality": 0.95,
        "is_gps_spoofed_or_denied": False,
    }
    resp = client.post("/v1/tactical/uav/analyze", json=uav_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["drone_id"] == "UAV-ALPHA-01"
    assert data["airworthiness_status"] == "NOMINAL"

    # 2. Starlink analyze
    starlink_payload = {
        "terminal_id": "STARLINK-01",
        "downlink_throughput_mbps": 120.0,
        "uplink_throughput_mbps": 25.0,
        "round_trip_latency_ms": 42.0,
        "packet_loss_rate": 0.002,
        "obstruction_fraction": 0.0,
        "snr_db": 10.5,
    }
    resp = client.post("/v1/tactical/starlink/analyze", json=starlink_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["terminal_id"] == "STARLINK-01"
    assert data["channel_state"] == "OPTIMAL"

    # 3. CUAS analyze
    cuas_payload = [
        {
            "sensor_id": "CUAS-SENS-01",
            "detected_target_id": "UAV-INTRUDER-99",
            "frequency_mhz": 2400.0,
            "protocol_fingerprint": "DJI_OCUSYNC",
            "rf_signal_strength_dbm": -45.0,
            "bearing_azimuth_deg": 180.0,
            "estimated_distance_m": 450.0,
        }
    ]
    resp = client.post("/v1/tactical/cuas/analyze?sector=SECTOR-NORTH", json=cuas_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["airspace_sector"] == "SECTOR-NORTH"
    assert data["detected_drones_count"] == 1


def test_embedded_endpoints(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=None))
    client = TestClient(app)

    # 1. Compile Package for ESP32-S3
    resp = client.post(
        "/v1/embedded/compile-package?target=esp32-s3&quantization=bitnet_1_58b"
    )
    assert resp.status_code == 200
    pkg = resp.json()
    assert pkg["target"] == "esp32-s3"
    assert "AEGIS_TARGET_HARDWARE" in pkg["c_header_source"]
    assert "nvs" in pkg["partition_csv_source"]

    # 2. Compile Package for ESP32-C6
    resp = client.post("/v1/embedded/compile-package?target=esp32-c6")
    assert resp.status_code == 200
    pkg = resp.json()
    assert pkg["target"] == "esp32-c6"

    # 3. Micro-telemetry decode endpoint
    frame_bytes = CompactBinaryProtocolCodec.encode(
        node_id=101,
        sequence_id=55,
        timestamp_unix=1700000000,
        latitude=45.123456,
        longitude=-75.654321,
        altitude_m=150,
        threat_flags=0x01,
        risk_score=0.75,
        rssi_dbm=-65,
        battery_pct=88,
    )
    hex_str = frame_bytes.hex()
    resp = client.post(f"/v1/embedded/micro-telemetry/decode?hex_frame={hex_str}")
    assert resp.status_code == 200
    telemetry = resp.json()
    assert telemetry["node_id"] == 101
    assert telemetry["battery_level_pct"] == 88
    assert telemetry["crc_valid"] is True

    # Bad frame decode
    resp_bad = client.post("/v1/embedded/micro-telemetry/decode?hex_frame=deadbeef")
    assert resp_bad.status_code == 400


def test_edge_manifest_and_sync_endpoints(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=None))
    client = TestClient(app)

    # 1. Edge manifest
    resp = client.get("/v1/edge/manifest")
    assert resp.status_code == 200
    manifest = resp.json()
    assert "node_id" in manifest
    assert "ledger_sequence" in manifest

    # 2. Edge sync
    sync_payload = {
        "node_id": "remote-edge-node-02",
        "ledger_sequence": 10,
        "head_block_hash": "a" * 64,
        "active_snapshots": {},
        "timestamp_unix": 1700000000,
    }
    resp = client.post("/v1/edge/sync", json=sync_payload)
    assert resp.status_code == 200
    res = resp.json()
    assert res["status"] in {"IN_SYNC", "BEHIND", "AHEAD", "SYNC_ACCEPTED"}
