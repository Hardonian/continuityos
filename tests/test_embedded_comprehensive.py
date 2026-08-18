from __future__ import annotations

import pytest

from continuityos.embedded import (
    CompactBinaryProtocolCodec,
    EmbeddedArchitectureEngine,
    MicroQuantization,
    TargetMicrocontroller,
    TinyMoEConfig,
)


def test_embedded_riscv_and_arm_layouts() -> None:
    engine = EmbeddedArchitectureEngine()

    # 1. RISCV Generic
    riscv_layout = engine.build_memory_layout(TargetMicrocontroller.RISCV_GENERIC)
    assert riscv_layout.target == TargetMicrocontroller.RISCV_GENERIC
    assert riscv_layout.flash_total_bytes == 32 * 1024 * 1024
    assert riscv_layout.max_model_parameters == 65_000_000

    # 2. ARM Cortex-M55
    arm_layout = engine.build_memory_layout(TargetMicrocontroller.CORTEX_M55)
    assert arm_layout.target == TargetMicrocontroller.CORTEX_M55

    # 3. Compile package for RISCV
    pkg_riscv = engine.compile_package(
        TargetMicrocontroller.RISCV_GENERIC,
        TinyMoEConfig(quantization=MicroQuantization.INT8_SYMMETRIC),
    )
    assert pkg_riscv.estimated_tokens_per_second > 10.0
    assert "AEGIS_QUANT_INT8_SYMM" in pkg_riscv.c_header_source


def test_compact_binary_protocol_codec_corruptions() -> None:
    # 1. Valid encode
    frame = CompactBinaryProtocolCodec.encode(
        node_id=42,
        sequence_id=1,
        timestamp_unix=1690000000,
        latitude=60.123456,
        longitude=24.654321,
        altitude_m=50,
        threat_flags=0x07,
        risk_score=0.92,
        rssi_dbm=-70,
        battery_pct=95,
    )
    assert len(frame) == CompactBinaryProtocolCodec.FRAME_SIZE

    decoded = CompactBinaryProtocolCodec.decode(frame)
    assert decoded.node_id == 42
    assert decoded.crc_valid is True
    assert decoded.battery_level_pct == 95

    # 2. Invalid frame length
    with pytest.raises(ValueError, match="Invalid frame size"):
        CompactBinaryProtocolCodec.decode(b"\x00" * 10)

    # 3. Corrupted payload CRC detection
    corrupted_frame = bytearray(frame)
    corrupted_frame[5] ^= 0xFF  # Flip bit in payload
    decoded_corrupt = CompactBinaryProtocolCodec.decode(bytes(corrupted_frame))
    assert decoded_corrupt.crc_valid is False
