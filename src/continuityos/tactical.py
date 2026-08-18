"""Tactical Multi-Domain Surveillance & Communication Channels.

Provides:
  1. UAVTacticalEngine: 3D kinematics, optical flow, EO/IR payload telemetry, and GPS-denied navigation tracking.
  2. StarlinkTacticalEngine: LEO constellation latency, beam switching Doppler jitter, downlink throughput, and Ku/Ka rain fade attenuation.
  3. CUASDefenseEngine: Counter-UAS RF spectral sniffing, micro-Doppler radar/acoustic detection, protocol fingerprinting, and interdiction telemetry.
  4. TacticalFusionBridge: Converts tactical telemetry into standardized Sovereign Observation records.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from continuityos.domain import (
    AssertionClass,
    GeoPoint,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.threat import ThreatSeverity


class UAVTelemetryFrame(BaseModel):
    """Real-time UAV / Drone flight kinematics and sensor payload telemetry."""

    drone_id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    altitude_m_msl: float
    ground_speed_mps: float = Field(ge=0.0)
    climb_rate_mps: float = Field(default=0.0)
    roll_deg: float = Field(ge=-180.0, le=180.0, default=0.0)
    pitch_deg: float = Field(ge=-90.0, le=90.0, default=0.0)
    yaw_deg: float = Field(ge=0.0, le=360.0, default=0.0)
    battery_state_of_charge: float = Field(ge=0.0, le=1.0)
    rf_link_margin_db: float = Field(default=25.0)
    optical_flow_quality: float = Field(ge=0.0, le=1.0, default=0.95)
    eoir_detections_count: int = Field(ge=0, default=0)
    is_gps_spoofed_or_denied: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UAVSurveillanceAssessment(BaseModel):
    """Evaluated tactical UAV operational status and mission risk."""

    drone_id: str
    airworthiness_status: (
        str  # "NOMINAL", "DEGRADED", "CRITICAL_RETURN_TO_BASE", "EMERGENCY_LANDING"
    )
    swarm_cohesion_score: float = Field(ge=0.0, le=1.0)
    link_health_score: float = Field(ge=0.0, le=1.0)
    navigation_integrity_score: float = Field(ge=0.0, le=1.0)
    tactical_risk_score: float = Field(ge=0.0, le=1.0)
    indicators: list[str] = Field(default_factory=list)
    advisory_directive: str


class UAVTacticalEngine:
    """Evaluates UAV fleet surveillance, GPS denial, and flight trajectory integrity."""

    def analyze_frame(self, frame: UAVTelemetryFrame) -> UAVSurveillanceAssessment:
        indicators: list[str] = []
        risk_components: list[float] = []

        # 1. Evaluate RF link margin
        if frame.rf_link_margin_db < 6.0:
            indicators.append(
                f"Severe RF command/telemetry link degradation ({frame.rf_link_margin_db:.1f} dB margin)"
            )
            link_health = 0.2
            risk_components.append(0.8)
        elif frame.rf_link_margin_db < 12.0:
            indicators.append(f"Moderate RF attenuation ({frame.rf_link_margin_db:.1f} dB margin)")
            link_health = 0.6
            risk_components.append(0.4)
        else:
            link_health = 0.95
            risk_components.append(0.05)

        # 2. Evaluate GPS denial & Optical Flow / VIO backup
        if frame.is_gps_spoofed_or_denied:
            indicators.append(
                "GPS/GNSS PNT signal denied or spoofed; relying on Optical Flow / Visual-Inertial Odometry"
            )
            if frame.optical_flow_quality < 0.4:
                indicators.append(
                    f"Optical flow quality degraded ({frame.optical_flow_quality:.2f}); drift accumulation critical"
                )
                nav_integrity = 0.2
                risk_components.append(0.9)
            else:
                nav_integrity = 0.7
                risk_components.append(0.35)
        else:
            nav_integrity = 0.98
            risk_components.append(0.02)

        # 3. Evaluate Battery reserve & flight envelope
        if frame.battery_state_of_charge < 0.15:
            indicators.append(f"Battery critically low ({frame.battery_state_of_charge:.1%})")
            risk_components.append(0.95)
            status = "CRITICAL_RETURN_TO_BASE"
            advisory = (
                "Initiate immediate automated Return-to-Base (RTB) on secondary INS waypoint vector"
            )
        elif frame.battery_state_of_charge < 0.25:
            indicators.append(f"Battery reserve caution ({frame.battery_state_of_charge:.1%})")
            risk_components.append(0.4)
            status = "DEGRADED"
            advisory = "Reroute patrol trajectory towards primary recovery staging zone"
        else:
            status = "NOMINAL"
            advisory = "Maintain tactical surveillance orbit; link and sensor payloads verified"

        # 4. Swarm cohesion & Kinematic envelope
        if abs(frame.pitch_deg) > 45.0 or abs(frame.roll_deg) > 60.0:
            indicators.append(
                f"Kinematic flight envelope near stall limit (Pitch={frame.pitch_deg:.1f}°, Roll={frame.roll_deg:.1f}°)"
            )
            risk_components.append(0.7)
            status = "DEGRADED"

        total_risk = round(sum(risk_components) / max(1, len(risk_components)), 3)
        swarm_cohesion = round(max(0.0, 1.0 - total_risk * 0.8), 2)

        if total_risk >= 0.75:
            status = "CRITICAL_RETURN_TO_BASE"

        return UAVSurveillanceAssessment(
            drone_id=frame.drone_id,
            airworthiness_status=status,
            swarm_cohesion_score=swarm_cohesion,
            link_health_score=round(link_health, 2),
            navigation_integrity_score=round(nav_integrity, 2),
            tactical_risk_score=total_risk,
            indicators=indicators,
            advisory_directive=advisory,
        )


class StarlinkTelemetry(BaseModel):
    """Live Starlink / LEO Constellation SATCOM telemetry."""

    terminal_id: str
    downlink_throughput_mbps: float = Field(ge=0.0)
    uplink_throughput_mbps: float = Field(ge=0.0)
    round_trip_latency_ms: float = Field(ge=0.0)
    packet_loss_rate: float = Field(ge=0.0, le=1.0)
    obstruction_fraction: float = Field(ge=0.0, le=1.0, default=0.0)
    snr_db: float = Field(default=9.5)
    beam_handover_jitter_ms: float = Field(ge=0.0, default=5.0)
    rain_fade_attenuation_db: float = Field(ge=0.0, default=0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StarlinkAssessment(BaseModel):
    """Evaluated Starlink SATCOM channel reliability and corridor availability."""

    terminal_id: str
    channel_state: str  # "OPTIMAL", "DEGRADED_LATENCY", "RAIN_FADE_ATTENUATED", "BEAM_STEERING_DENIED", "OFFLINE"
    availability_score: float = Field(ge=0.0, le=1.0)
    effective_bandwidth_score: float = Field(ge=0.0, le=1.0)
    latency_threat_score: float = Field(ge=0.0, le=1.0)
    indicators: list[str] = Field(default_factory=list)
    advisory: str


class StarlinkTacticalEngine:
    """Analyzes Starlink / LEO satellite constellation throughput, latency, and rain fade."""

    def evaluate_channel(self, telemetry: StarlinkTelemetry) -> StarlinkAssessment:
        indicators: list[str] = []
        risk = 0.0

        # 1. Latency & Jitter
        if telemetry.round_trip_latency_ms > 120.0:
            indicators.append(
                f"High LEO RTT latency ({telemetry.round_trip_latency_ms:.1f} ms) exceeds tactical SLA"
            )
            risk += 0.35
        elif telemetry.round_trip_latency_ms > 65.0:
            indicators.append(f"Elevated latency ({telemetry.round_trip_latency_ms:.1f} ms)")
            risk += 0.15

        if telemetry.beam_handover_jitter_ms > 25.0:
            indicators.append(
                f"Satellite handover jitter spike ({telemetry.beam_handover_jitter_ms:.1f} ms)"
            )
            risk += 0.2

        # 2. Rain fade / Ku/Ka band attenuation & Obstructions
        if telemetry.rain_fade_attenuation_db > 8.0:
            indicators.append(
                f"Severe atmospheric rain fade attenuation ({telemetry.rain_fade_attenuation_db:.1f} dB)"
            )
            risk += 0.3

        if telemetry.obstruction_fraction > 0.10:
            indicators.append(
                f"Sky view obstruction ({telemetry.obstruction_fraction:.1%}) causing intermittent dropouts"
            )
            risk += 0.4

        if telemetry.packet_loss_rate > 0.05:
            indicators.append(f"High packet loss ({telemetry.packet_loss_rate:.1%})")
            risk += 0.35

        # Throughput rating
        bw_score = min(1.0, telemetry.downlink_throughput_mbps / 100.0)
        threat_score = min(1.0, risk)
        avail_score = max(0.0, 1.0 - threat_score)

        if avail_score < 0.2:
            state = "OFFLINE"
            advisory = "Failover tactical comms to secondary Iridium Certus / terrestrial HF mesh"
        elif telemetry.rain_fade_attenuation_db > 8.0:
            state = "RAIN_FADE_ATTENUATED"
            advisory = "Enable adaptive coding and modulation (ACM) & prioritize telemetry over video feeds"
        elif telemetry.round_trip_latency_ms > 100.0:
            state = "DEGRADED_LATENCY"
            advisory = "Buffer telemetry frames; suppress non-critical drone payload streams"
        else:
            state = "OPTIMAL"
            advisory = "LEO Constellation locked; beam handover nominal"

        return StarlinkAssessment(
            terminal_id=telemetry.terminal_id,
            channel_state=state,
            availability_score=round(avail_score, 2),
            effective_bandwidth_score=round(bw_score, 2),
            latency_threat_score=round(threat_score, 2),
            indicators=indicators,
            advisory=advisory,
        )


class CUASDetectionEvent(BaseModel):
    """Counter-UAS (Anti-Drone) sensor detection event."""

    sensor_id: str
    detected_target_id: str
    frequency_mhz: float
    protocol_fingerprint: str  # "DJI_OCUSYNC", "EXPRESS_LRS", "TBS_CROSSFIRE", "CUSTOM_FHSS", "UNKNOWN_DIRECT_SEQUENCE"
    rf_signal_strength_dbm: float
    bearing_azimuth_deg: float = Field(ge=0.0, le=360.0)
    elevation_deg: float = Field(ge=-90.0, le=90.0, default=15.0)
    estimated_distance_m: float = Field(ge=0.0)
    radar_cross_section_sqm: float = Field(ge=0.0, default=0.01)
    micro_doppler_blade_count: int = Field(ge=0, default=4)
    is_swarm_formation: bool = False
    interdiction_active: bool = False
    interdiction_type: str = (
        "NONE"  # "NONE", "RF_JAMMING_ACTIVE", "GNSS_SPOOF_ACTIVE", "KINETIC_INTERCEPT"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CUASAssessment(BaseModel):
    """Synthesized Counter-UAS airspace threat rating."""

    airspace_sector: str
    threat_severity: ThreatSeverity
    detected_drones_count: int
    swarm_likelihood: float = Field(ge=0.0, le=1.0)
    electronic_warfare_active: bool
    recommended_interdiction: str
    tactical_summary: str


class CUASDefenseEngine:
    """Evaluates Counter-UAS (Anti-Drone) RF surveillance, micro-Doppler radar, and swarm threats."""

    def analyze_events(self, sector: str, events: list[CUASDetectionEvent]) -> CUASAssessment:
        if not events:
            return CUASAssessment(
                airspace_sector=sector,
                threat_severity=ThreatSeverity(
                    level="NOMINAL",
                    score=0.05,
                    confidence=0.95,
                    indicators=[
                        "Airspace clear; no unauthorized RF or radar drone signatures detected"
                    ],
                    remediation_recommendation="",
                ),
                detected_drones_count=0,
                swarm_likelihood=0.0,
                electronic_warfare_active=False,
                recommended_interdiction="Maintain passive RF spectral monitoring",
                tactical_summary=f"Sector {sector} airspace nominal.",
            )

        indicators: list[str] = []
        threat_score = 0.0
        swarm_count = len(events)
        is_swarm = swarm_count >= 3 or any(e.is_swarm_formation for e in events)
        ew_active = any(e.interdiction_active for e in events)

        for event in events:
            sig_name = event.protocol_fingerprint
            indicators.append(
                f"Target {event.detected_target_id} [{sig_name}]: Distance={event.estimated_distance_m:.0f}m, "
                f"RCS={event.radar_cross_section_sqm:.3f}m², Signal={event.rf_signal_strength_dbm:.1f}dBm"
            )

            # Weight by distance and protocol
            if event.estimated_distance_m < 500.0:
                threat_score += 0.40
            elif event.estimated_distance_m < 2000.0:
                threat_score += 0.20
            else:
                threat_score += 0.10

            if sig_name in {"CUSTOM_FHSS", "UNKNOWN_DIRECT_SEQUENCE"}:
                threat_score += 0.25
                indicators.append(
                    f"Target {event.detected_target_id} using military-grade frequency-hopping spread spectrum"
                )

        if is_swarm:
            threat_score += 0.35
            indicators.append(
                f"Swarm attack pattern recognized: {swarm_count} coordinated targets in sector"
            )

        threat_score = min(1.0, threat_score)
        level = (
            "CRITICAL" if threat_score >= 0.75 else ("HIGH" if threat_score >= 0.45 else "MEDIUM")
        )

        if threat_score >= 0.75:
            remed = "Authorize directional C-UAS RF barrage jamming on 2.4/5.8GHz and 868/915MHz bands; prepare kinetic net countermeasures"
        elif threat_score >= 0.45:
            remed = "Activate targeted RF protocol disruption; focus PTZ EO/IR tracking cameras on bearing"
        else:
            remed = "Track target trajectory and log RF signature"

        summary = (
            f"C-UAS Threat Level {level} in {sector}: {swarm_count} active targets. "
            f"Swarm pattern: {'CONFIRMED' if is_swarm else 'UNLIKELY'}. "
            f"Interdiction state: {'ACTIVE' if ew_active else 'STANDBY'}."
        )

        return CUASAssessment(
            airspace_sector=sector,
            threat_severity=ThreatSeverity(
                level=level,
                score=round(threat_score, 3),
                confidence=0.94,
                indicators=indicators,
                remediation_recommendation=remed,
            ),
            detected_drones_count=swarm_count,
            swarm_likelihood=0.9 if is_swarm else min(0.4, swarm_count * 0.15),
            electronic_warfare_active=ew_active,
            recommended_interdiction=remed,
            tactical_summary=summary,
        )


class TacticalFusionBridge:
    """Bridges tactical surveillance streams into standardized Sovereign Observation records."""

    @staticmethod
    def uav_to_observations(
        assessment: UAVSurveillanceAssessment,
        frame: UAVTelemetryFrame,
        source_id: str = "tactical-uav-fleet",
    ) -> list[Observation]:
        now = datetime.now(UTC)
        prov_hash = hashlib.sha256(f"{frame.drone_id}:{frame.timestamp}".encode()).hexdigest()
        prov = Provenance(
            uri=f"tactical://uav/{frame.drone_id}",
            retrieved_at=now,
            content_sha256=prov_hash,
            licence="sovereign-tactical",
        )
        location = GeoPoint(latitude=frame.latitude, longitude=frame.longitude)

        return [
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.TACTICAL_SURVEILLANCE,
                metric=MetricName.UAV_LINK_MARGIN,
                value=max(0.0, frame.rf_link_margin_db),
                unit="dB",
                observed_at=now,
                location=location,
                confidence=0.95,
                provenance=prov,
                metadata={"drone_id": frame.drone_id, "status": assessment.airworthiness_status},
            ),
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.TACTICAL_SURVEILLANCE,
                metric=MetricName.UAV_SWARM_COHESION,
                value=assessment.swarm_cohesion_score,
                unit="score",
                observed_at=now,
                location=location,
                confidence=0.92,
                provenance=prov,
                metadata={"drone_id": frame.drone_id},
            ),
        ]

    @staticmethod
    def starlink_to_observations(
        assessment: StarlinkAssessment,
        telemetry: StarlinkTelemetry,
        source_id: str = "starlink-leo-network",
    ) -> list[Observation]:
        now = datetime.now(UTC)
        prov_hash = hashlib.sha256(
            f"{telemetry.terminal_id}:{telemetry.timestamp}".encode()
        ).hexdigest()
        prov = Provenance(
            uri=f"tactical://starlink/{telemetry.terminal_id}",
            retrieved_at=now,
            content_sha256=prov_hash,
            licence="sovereign-tactical",
        )

        return [
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.LEO_SATCOM,
                metric=MetricName.STARLINK_LATENCY_MS,
                value=telemetry.round_trip_latency_ms,
                unit="ms",
                observed_at=now,
                confidence=0.96,
                provenance=prov,
                metadata={"terminal_id": telemetry.terminal_id, "state": assessment.channel_state},
            ),
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.LEO_SATCOM,
                metric=MetricName.STARLINK_DOWNLINK_MBPS,
                value=telemetry.downlink_throughput_mbps,
                unit="mbps",
                observed_at=now,
                confidence=0.96,
                provenance=prov,
                metadata={"terminal_id": telemetry.terminal_id},
            ),
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.LEO_SATCOM,
                metric=MetricName.STARLINK_OBSTRUCTION_RATE,
                value=telemetry.obstruction_fraction,
                unit="fraction",
                observed_at=now,
                confidence=0.95,
                provenance=prov,
                metadata={"terminal_id": telemetry.terminal_id},
            ),
        ]

    @staticmethod
    def cuas_to_observations(
        assessment: CUASAssessment,
        sector: str,
        source_id: str = "cuas-air-defense-sensor",
    ) -> list[Observation]:
        now = datetime.now(UTC)
        prov_hash = hashlib.sha256(f"{sector}:{now.isoformat()}".encode()).hexdigest()
        prov = Provenance(
            uri=f"tactical://cuas/{sector}",
            retrieved_at=now,
            content_sha256=prov_hash,
            licence="sovereign-tactical",
        )

        return [
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.COUNTER_UAS,
                metric=MetricName.CUAS_THREAT_DENSITY,
                value=assessment.threat_severity.score,
                unit="score",
                observed_at=now,
                confidence=0.94,
                provenance=prov,
                metadata={"sector": sector, "level": assessment.threat_severity.level},
            ),
            Observation(
                source_id=source_id,
                source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
                assertion_class=AssertionClass.COUNTER_UAS,
                metric=MetricName.CUAS_JAMMING_ACTIVE,
                value=1.0 if assessment.electronic_warfare_active else 0.0,
                unit="binary",
                observed_at=now,
                confidence=0.99,
                provenance=prov,
                metadata={"sector": sector},
            ),
        ]
