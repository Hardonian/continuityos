from __future__ import annotations

from datetime import UTC, datetime

from continuityos.tactical import (
    CUASDefenseEngine,
    CUASDetectionEvent,
    StarlinkTacticalEngine,
    StarlinkTelemetry,
    UAVTacticalEngine,
    UAVTelemetryFrame,
)


def test_uav_moderate_attenuation_and_caution_battery() -> None:
    engine = UAVTacticalEngine()
    frame = UAVTelemetryFrame(
        drone_id="UAV-PATROL-02",
        latitude=60.0,
        longitude=25.0,
        altitude_m_msl=150.0,
        ground_speed_mps=12.0,
        battery_state_of_charge=0.20,  # Caution level (0.15 - 0.25)
        rf_link_margin_db=9.0,  # Moderate attenuation (6.0 - 12.0)
        optical_flow_quality=0.85,
        is_gps_spoofed_or_denied=False,
    )
    assessment = engine.analyze_frame(frame)
    assert assessment.airworthiness_status == "DEGRADED"
    assert assessment.link_health_score == 0.6
    assert "Reroute patrol" in assessment.advisory_directive


def test_uav_gps_denied_good_optical_flow() -> None:
    engine = UAVTacticalEngine()
    frame = UAVTelemetryFrame(
        drone_id="UAV-VIO-03",
        latitude=60.0,
        longitude=25.0,
        altitude_m_msl=100.0,
        ground_speed_mps=10.0,
        battery_state_of_charge=0.80,
        rf_link_margin_db=20.0,
        optical_flow_quality=0.80,  # >= 0.4 good optical flow backup
        is_gps_spoofed_or_denied=True,
    )
    assessment = engine.analyze_frame(frame)
    assert assessment.navigation_integrity_score == 0.70
    assert any("Optical Flow" in ind for ind in assessment.indicators)


def test_uav_stall_envelope_limits() -> None:
    engine = UAVTacticalEngine()
    frame = UAVTelemetryFrame(
        drone_id="UAV-ACROBAT-05",
        latitude=60.0,
        longitude=25.0,
        altitude_m_msl=200.0,
        ground_speed_mps=30.0,
        pitch_deg=50.0,  # Stall pitch > 45
        roll_deg=70.0,  # Stall roll > 60
        battery_state_of_charge=0.90,
        rf_link_margin_db=22.0,
    )
    assessment = engine.analyze_frame(frame)
    assert assessment.airworthiness_status in {"DEGRADED", "CRITICAL_RETURN_TO_BASE"}
    assert any("near stall" in ind for ind in assessment.indicators)


def test_starlink_elevated_latency_and_handover_jitter() -> None:
    engine = StarlinkTacticalEngine()
    tel = StarlinkTelemetry(
        terminal_id="DISHY-JITTER-01",
        downlink_throughput_mbps=85.0,
        uplink_throughput_mbps=15.0,
        round_trip_latency_ms=75.0,  # Elevated latency (65..120)
        packet_loss_rate=0.01,
        beam_handover_jitter_ms=30.0,  # Jitter spike > 25ms
    )
    assessment = engine.evaluate_channel(tel)
    assert any("Elevated latency" in ind for ind in assessment.indicators)
    assert any("handover jitter spike" in ind for ind in assessment.indicators)


def test_starlink_complete_channel_offline() -> None:
    engine = StarlinkTacticalEngine()
    tel = StarlinkTelemetry(
        terminal_id="DISHY-BLACKOUT-02",
        downlink_throughput_mbps=0.5,
        uplink_throughput_mbps=0.1,
        round_trip_latency_ms=450.0,
        packet_loss_rate=0.45,
        obstruction_fraction=0.80,
        rain_fade_attenuation_db=15.0,
        beam_handover_jitter_ms=60.0,
    )
    assessment = engine.evaluate_channel(tel)
    assert assessment.channel_state == "OFFLINE"
    assert "Failover tactical comms" in assessment.advisory


def test_starlink_degraded_latency_state() -> None:
    engine = StarlinkTacticalEngine()
    tel = StarlinkTelemetry(
        terminal_id="DISHY-DEGRADED-03",
        downlink_throughput_mbps=50.0,
        uplink_throughput_mbps=10.0,
        round_trip_latency_ms=105.0,  # > 100ms
        packet_loss_rate=0.01,
        rain_fade_attenuation_db=2.0,  # <= 8.0
    )
    assessment = engine.evaluate_channel(tel)
    assert assessment.channel_state == "DEGRADED_LATENCY"
    assert "Buffer telemetry frames" in assessment.advisory


def test_cuas_distant_targets_and_medium_threat() -> None:
    engine = CUASDefenseEngine()
    now = datetime.now(UTC)
    events = [
        CUASDetectionEvent(
            sensor_id="CUAS-DISTANT-01",
            detected_target_id="DRONE-FAR-01",
            frequency_mhz=2400.0,
            protocol_fingerprint="DJI_OCUSYNC",
            rf_signal_strength_dbm=-78.0,
            bearing_azimuth_deg=90.0,
            estimated_distance_m=2500.0,  # > 2000m distant
            radar_cross_section_sqm=0.01,
            is_swarm_formation=False,
            timestamp=now,
        ),
        CUASDetectionEvent(
            sensor_id="CUAS-DISTANT-02",
            detected_target_id="DRONE-MID-02",
            frequency_mhz=2400.0,
            protocol_fingerprint="DJI_OCUSYNC",
            rf_signal_strength_dbm=-65.0,
            bearing_azimuth_deg=95.0,
            estimated_distance_m=1200.0,  # 500..2000m mid
            radar_cross_section_sqm=0.01,
            is_swarm_formation=False,
            timestamp=now,
        ),
    ]
    assessment = engine.analyze_events("SECTOR-EAST", events)
    assert assessment.threat_severity.level in {"MEDIUM", "HIGH"}
    assert assessment.detected_drones_count == 2
    assert assessment.electronic_warfare_active is False
