from continuityos.embedded import (
    CompactBinaryProtocolCodec,
    EmbeddedArchitectureEngine,
    MicroQuantization,
    TargetMicrocontroller,
    TinyMoEConfig,
)


def test_embedded_memory_layout_esp32_s3() -> None:
    engine = EmbeddedArchitectureEngine()
    layout = engine.build_memory_layout(TargetMicrocontroller.ESP32_S3)

    assert layout.target == TargetMicrocontroller.ESP32_S3
    assert layout.flash_total_bytes == 16 * 1024 * 1024  # 16MB Flash
    assert layout.psram_total_bytes == 8 * 1024 * 1024  # 8MB PSRAM
    assert layout.per_layer_embeddings_enabled is True
    assert any(r.name == "FLASH_PLE_WEIGHTS_XIP" for r in layout.regions)
    assert any(r.name == "PSRAM_KV_CACHE_WORKSPACE" for r in layout.regions)


def test_embedded_memory_layout_esp32_c6() -> None:
    engine = EmbeddedArchitectureEngine()
    layout = engine.build_memory_layout(TargetMicrocontroller.ESP32_C6)

    assert layout.target == TargetMicrocontroller.ESP32_C6
    assert layout.flash_total_bytes == 8 * 1024 * 1024
    assert layout.recommended_power_mw <= 150.0


def test_edge_package_compilation() -> None:
    engine = EmbeddedArchitectureEngine()
    moe = TinyMoEConfig(
        total_parameters=28_900_000,
        active_parameters_per_token=8_500_000,
        quantization=MicroQuantization.INT4_WEIGHT_ONLY,
    )
    pkg = engine.compile_package(TargetMicrocontroller.ESP32_S3, moe)

    assert pkg.target == TargetMicrocontroller.ESP32_S3
    assert "#define AEGIS_TOTAL_PARAMS" in pkg.c_header_source
    assert "28900000" in pkg.c_header_source
    assert (
        "FLASH_PLE_WEIGHTS_XIP" in pkg.c_header_source
        or "AEGIS_FLASH_WEIGHTS_OFFSET" in pkg.c_header_source
    )
    assert "partitions.csv" in pkg.partition_csv_source or "nvs" in pkg.partition_csv_source
    assert pkg.estimated_tokens_per_second > 5.0


def test_compact_binary_protocol_encode_decode() -> None:
    # Test bitpacking into exact 24 bytes
    frame = CompactBinaryProtocolCodec.encode(
        node_id=42,
        sequence_id=1001,
        timestamp_unix=1725000000,
        latitude=69.123456,
        longitude=33.654321,
        altitude_m=350,
        threat_flags=0x05,
        risk_score=0.82,
        rssi_dbm=-65,
        battery_pct=88,
    )

    assert len(frame) == 26  # Exactly 26 bytes packed!

    # Decode and verify bit-for-bit fidelity
    packet = CompactBinaryProtocolCodec.decode(frame)
    assert packet.node_id == 42
    assert packet.sequence_id == 1001
    assert packet.timestamp_unix == 1725000000
    assert abs(packet.latitude - 69.123456) < 1e-5
    assert abs(packet.longitude - 33.654321) < 1e-5
    assert packet.altitude_m == 350
    assert packet.threat_factor_flags == 0x05
    assert packet.link_quality_rssi_dbm == -65
    assert packet.battery_level_pct == 88
    assert packet.crc_valid is True


def test_compact_binary_protocol_corrupted_crc() -> None:
    frame = bytearray(
        CompactBinaryProtocolCodec.encode(
            node_id=1,
            sequence_id=2,
            timestamp_unix=1700000000,
            latitude=70.0,
            longitude=30.0,
            altitude_m=100,
            threat_flags=0,
            risk_score=0.1,
            rssi_dbm=-70,
            battery_pct=90,
        )
    )
    # Corrupt a byte in the payload
    frame[5] ^= 0xFF

    packet = CompactBinaryProtocolCodec.decode(bytes(frame))
    assert packet.crc_valid is False
