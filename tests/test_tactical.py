from datetime import UTC, datetime

from continuityos.domain import AssertionClass, MetricName, SourceTrust
from continuityos.tactical import (
    CUASDefenseEngine,
    CUASDetectionEvent,
    StarlinkTacticalEngine,
    StarlinkTelemetry,
    TacticalFusionBridge,
    UAVTacticalEngine,
    UAVTelemetryFrame,
)


def test_uav_tactical_engine_nominal() -> None:
    engine = UAVTacticalEngine()
    frame = UAVTelemetryFrame(
        drone_id="UAV-RECON-01",
        latitude=68.5,
        longitude=33.2,
        altitude_m_msl=250.0,
        ground_speed_mps=18.5,
        climb_rate_mps=0.5,
        roll_deg=5.0,
        pitch_deg=2.0,
        yaw_deg=180.0,
        battery_state_of_charge=0.85,
        rf_link_margin_db=28.0,
        optical_flow_quality=0.98,
        eoir_detections_count=2,
        is_gps_spoofed_or_denied=False,
    )
    assessment = engine.analyze_frame(frame)
    assert assessment.airworthiness_status == "NOMINAL"
    assert assessment.swarm_cohesion_score > 0.8
    assert assessment.link_health_score > 0.9
    assert assessment.tactical_risk_score < 0.2

    # Test observation generation
    obs = TacticalFusionBridge.uav_to_observations(assessment, frame)
    assert len(obs) == 2
    assert obs[0].assertion_class == AssertionClass.TACTICAL_SURVEILLANCE
    assert obs[0].metric == MetricName.UAV_LINK_MARGIN
    assert obs[0].source_trust == SourceTrust.AUTHENTICATED_OPERATOR


def test_uav_tactical_engine_gps_denial_and_low_battery() -> None:
    engine = UAVTacticalEngine()
    frame = UAVTelemetryFrame(
        drone_id="UAV-ASSAULT-04",
        latitude=68.5,
        longitude=33.2,
        altitude_m_msl=120.0,
        ground_speed_mps=15.0,
        battery_state_of_charge=0.12,  # Critically low
        rf_link_margin_db=4.5,  # Degraded RF
        optical_flow_quality=0.30,  # Poor optical flow
        is_gps_spoofed_or_denied=True,  # Spoofed/Denied
    )
    assessment = engine.analyze_frame(frame)
    assert assessment.airworthiness_status == "CRITICAL_RETURN_TO_BASE"
    assert assessment.tactical_risk_score >= 0.70
    assert any("Return-to-Base" in assessment.advisory_directive for _ in [1])


def test_starlink_tactical_engine() -> None:
    engine = StarlinkTacticalEngine()

    # Nominal telemetry
    nom_tel = StarlinkTelemetry(
        terminal_id="DISHY-TAC-01",
        downlink_throughput_mbps=145.0,
        uplink_throughput_mbps=22.0,
        round_trip_latency_ms=38.0,
        packet_loss_rate=0.005,
        obstruction_fraction=0.0,
        snr_db=11.2,
    )
    nom_eval = engine.evaluate_channel(nom_tel)
    assert nom_eval.channel_state == "OPTIMAL"
    assert nom_eval.availability_score >= 0.90

    # Rain fade & severe latency telemetry
    degraded_tel = StarlinkTelemetry(
        terminal_id="DISHY-TAC-02",
        downlink_throughput_mbps=12.0,
        uplink_throughput_mbps=2.0,
        round_trip_latency_ms=160.0,
        packet_loss_rate=0.08,
        obstruction_fraction=0.15,
        rain_fade_attenuation_db=11.5,
    )
    deg_eval = engine.evaluate_channel(degraded_tel)
    assert deg_eval.channel_state in {"RAIN_FADE_ATTENUATED", "DEGRADED_LATENCY", "OFFLINE"}
    assert deg_eval.latency_threat_score > 0.50

    obs = TacticalFusionBridge.starlink_to_observations(deg_eval, degraded_tel)
    assert len(obs) == 3
    assert any(o.metric == MetricName.STARLINK_LATENCY_MS for o in obs)


def test_cuas_anti_drone_defense() -> None:
    engine = CUASDefenseEngine()

    # Clear airspace
    clear_eval = engine.analyze_events("SECTOR-NORTH", [])
    assert clear_eval.threat_severity.level == "NOMINAL"
    assert clear_eval.detected_drones_count == 0

    # Hostile Swarm detected
    now = datetime.now(UTC)
    events = [
        CUASDetectionEvent(
            sensor_id="RF-DF-01",
            detected_target_id="DRONE-HOSTILE-01",
            frequency_mhz=2437.0,
            protocol_fingerprint="DJI_OCUSYNC",
            rf_signal_strength_dbm=-48.0,
            bearing_azimuth_deg=45.0,
            estimated_distance_m=350.0,
            radar_cross_section_sqm=0.02,
            is_swarm_formation=True,
            interdiction_active=True,
            interdiction_type="RF_JAMMING_ACTIVE",
            timestamp=now,
        ),
        CUASDetectionEvent(
            sensor_id="RF-DF-02",
            detected_target_id="DRONE-HOSTILE-02",
            frequency_mhz=868.0,
            protocol_fingerprint="CUSTOM_FHSS",
            rf_signal_strength_dbm=-42.0,
            bearing_azimuth_deg=47.0,
            estimated_distance_m=400.0,
            radar_cross_section_sqm=0.05,
            is_swarm_formation=True,
            interdiction_active=True,
            timestamp=now,
        ),
        CUASDetectionEvent(
            sensor_id="RADAR-MICRO-01",
            detected_target_id="DRONE-HOSTILE-03",
            frequency_mhz=5800.0,
            protocol_fingerprint="EXPRESS_LRS",
            rf_signal_strength_dbm=-55.0,
            bearing_azimuth_deg=44.0,
            estimated_distance_m=600.0,
            radar_cross_section_sqm=0.03,
            is_swarm_formation=True,
            timestamp=now,
        ),
    ]

    swarm_eval = engine.analyze_events("SECTOR-DEFENSE-A", events)
    assert swarm_eval.threat_severity.level in {"HIGH", "CRITICAL"}
    assert swarm_eval.detected_drones_count == 3
    assert swarm_eval.swarm_likelihood >= 0.8
    assert swarm_eval.electronic_warfare_active is True
    assert "jamming" in swarm_eval.recommended_interdiction.lower()

    obs = TacticalFusionBridge.cuas_to_observations(swarm_eval, "SECTOR-DEFENSE-A")
    assert len(obs) == 2
    assert any(o.metric == MetricName.CUAS_THREAT_DENSITY for o in obs)
