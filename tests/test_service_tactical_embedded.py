from __future__ import annotations

from fastapi.testclient import TestClient

from continuityos.config import Settings
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
    assert data["assessment"]["drone_id"] == "UAV-ALPHA-01"
    assert data["assessment"]["airworthiness_status"] == "NOMINAL"
    assert len(data["observations"]) == 2

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
    assert data["assessment"]["terminal_id"] == "STARLINK-01"
    assert data["assessment"]["channel_state"] == "OPTIMAL"

    # 3. CUAS analyze
    cuas_payload = {
        "sector": "SECTOR-NORTH",
        "events": [
            {
                "sensor_id": "CUAS-SENS-01",
                "detected_target_id": "UAV-INTRUDER-99",
                "frequency_mhz": 2400.0,
                "protocol_fingerprint": "DJI_OCUSYNC",
                "rf_signal_strength_dbm": -45.0,
                "bearing_azimuth_deg": 180.0,
                "estimated_distance_m": 450.0,
            }
        ],
    }
    resp = client.post("/v1/tactical/cuas/analyze", json=cuas_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["assessment"]["airspace_sector"] == "SECTOR-NORTH"
    assert data["assessment"]["detected_drones_count"] == 1


def test_embedded_endpoints(tmp_path) -> None:
    app = create_app(Settings(environment="test", data_dir=tmp_path, api_key=None))
    client = TestClient(app)

    # 1. Compile Package for ESP32-S3
    resp = client.post(
        "/v1/embedded/compile-package",
        json={"target": "esp32-s3", "moe_config": {"quantization": "bitnet_1_58b"}},
    )
    assert resp.status_code == 200
    pkg = resp.json()
    assert pkg["target"] == "esp32-s3"
    assert "AEGIS_TARGET_HARDWARE" in pkg["c_header_source"]
    assert "nvs" in pkg["partition_csv_source"]

    # 2. Compile Package for ESP32-C6
    resp = client.post("/v1/embedded/compile-package", json={"target": "esp32-c6"})
    assert resp.status_code == 200
    pkg = resp.json()
    assert pkg["target"] == "esp32-c6"

    # 3. Micro-telemetry encode endpoint
    encode_resp = client.post(
        "/v1/embedded/micro-telemetry/encode",
        json={
            "node_id": 101,
            "sequence_id": 55,
            "timestamp_unix": 1700000000,
            "latitude": 45.123456,
            "longitude": -75.654321,
            "altitude_m": 150,
            "threat_flags": 1,
            "risk_score": 0.75,
            "rssi_dbm": -65,
            "battery_pct": 88,
        },
    )
    assert encode_resp.status_code == 200
    hex_frame = encode_resp.json()["frame_hex"]

    # 4. Micro-telemetry decode endpoint
    decode_resp = client.post("/v1/embedded/micro-telemetry/decode", json={"frame_hex": hex_frame})
    assert decode_resp.status_code == 200
    telemetry = decode_resp.json()
    assert telemetry["node_id"] == 101
    assert telemetry["battery_level_pct"] == 88
    assert telemetry["crc_valid"] is True


def test_edge_manifest_and_sync_endpoints(tmp_path) -> None:
    app = create_app(
        Settings(environment="test", data_dir=tmp_path, api_key=None, edge_enabled=True)
    )
    client = TestClient(app)

    # 1. Edge manifest
    resp = client.get("/v1/edge/manifest")
    assert resp.status_code == 200
    manifest = resp.json()
    assert "peer_id" in manifest
    assert "snapshot_ids" in manifest

    # 2. Edge peers
    peer_resp = client.post("/v1/edge/peers", json={"url": "http://127.0.0.1:19000"})
    assert peer_resp.status_code == 200
    assert peer_resp.json()["status"] == "ok"
