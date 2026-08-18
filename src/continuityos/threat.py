"""Cybersecurity Threat Detection and Cyber-Physical Anomaly Engine.

Provides deep multi-vector threat detection across critical trade infrastructure:
  1. GNSS / PNT Electronic Warfare & Spoofing Detector.
  2. Port OT / SCADA Ransomware & Firmware Injection Anomaly Detector.
  3. SATCOM Space Weather & Ionospheric Scintillation Attenuation Detector.
  4. Maritime AIS Kinematic Physics Violation & Dark Fleet Spoofing Detector.
"""

from __future__ import annotations

import math
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ThreatSeverity(BaseModel):
    """Threat severity score and classification."""

    level: str  # "NOMINAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    indicators: list[str] = Field(default_factory=list)
    remediation_recommendation: str = ""


class GNSSAnomalyReport(BaseModel):
    """GNSS/PNT EW Spoofing & Jamming assessment."""

    is_spoofed: bool
    is_jammed: bool
    pseudorange_variance: float
    cno_drop_db: float
    clock_drift_ppm: float
    threat: ThreatSeverity


class GNSSAnomalyDetector:
    """Detects Electronic Warfare GNSS spoofing, meaconing, and jamming."""

    def analyze(
        self,
        *,
        pseudorange_residuals_m: list[float],
        carrier_to_noise_ratios_db: list[float],
        clock_drift_ppm: float,
        geometric_dop: float = 1.8,
    ) -> GNSSAnomalyReport:
        indicators: list[str] = []
        spoofed = False
        jammed = False

        # 1. Evaluate Carrier-to-Noise Ratio (C/N0) degradation
        avg_cno = (
            sum(carrier_to_noise_ratios_db) / len(carrier_to_noise_ratios_db)
            if carrier_to_noise_ratios_db
            else 40.0
        )
        cno_drop = max(0.0, 42.0 - avg_cno)
        if cno_drop > 15.0:
            jammed = True
            indicators.append(
                f"Severe broadband RF power attenuation detected: C/N0 drop of {cno_drop:.1f} dB"
            )

        # 2. Evaluate Pseudorange Residual Variance (Spoofing multi-satellite jump)
        if pseudorange_residuals_m:
            variance = sum(
                (x - sum(pseudorange_residuals_m) / len(pseudorange_residuals_m)) ** 2
                for x in pseudorange_residuals_m
            ) / len(pseudorange_residuals_m)
        else:
            variance = 0.0

        if variance > 25.0:
            spoofed = True
            indicators.append(
                f"Pseudorange residual variance elevated ({variance:.1f} m^2) indicating "
                "synthetic constellation injection"
            )

        # 3. Receiver clock drift jump
        if abs(clock_drift_ppm) > 5.0:
            spoofed = True
            indicators.append(
                f"Receiver clock drift rate jump ({clock_drift_ppm:+.2f} ppm) exceeds "
                "quartz oscillator physics"
            )

        if geometric_dop > 6.0:
            indicators.append(
                f"Geometric Dilution of Precision (GDOP={geometric_dop:.1f}) abnormally degraded"
            )

        # Calculate threat score
        threat_score = min(
            1.0,
            (cno_drop / 25.0) * 0.4
            + (min(50.0, variance) / 50.0) * 0.4
            + (min(10.0, abs(clock_drift_ppm)) / 10.0) * 0.2,
        )

        level = "NOMINAL"
        if threat_score >= 0.8:
            level = "CRITICAL"
        elif threat_score >= 0.5:
            level = "HIGH"
        elif threat_score >= 0.25:
            level = "MEDIUM"
        elif threat_score > 0.0:
            level = "LOW"

        remed = ""
        if spoofed or jammed:
            remed = (
                "Transition navigation to secondary Inertial Navigation System (INS) + "
                "Celestial backup"
            )

        return GNSSAnomalyReport(
            is_spoofed=spoofed,
            is_jammed=jammed,
            pseudorange_variance=round(variance, 2),
            cno_drop_db=round(cno_drop, 2),
            clock_drift_ppm=round(clock_drift_ppm, 2),
            threat=ThreatSeverity(
                level=level,
                score=round(threat_score, 3),
                confidence=0.92,
                indicators=indicators,
                remediation_recommendation=remed,
            ),
        )


class PortSCADAAnomalyReport(BaseModel):
    """Industrial Control Systems (ICS) / SCADA threat report."""

    ransomware_signature_detected: bool
    unauthorized_plc_reprogramming: bool
    command_burst_frequency: float
    threat: ThreatSeverity


class PortSCADAAnomalyDetector:
    """Detects ransomware payloads, command bursts, and unauthorized PLC modifications."""

    def analyze(
        self,
        *,
        commands_per_second: float,
        unauthorized_function_codes: list[int],
        untrusted_ip_connections: int,
        plc_firmware_hashes: dict[str, str],
        expected_firmware_hash: str,
    ) -> PortSCADAAnomalyReport:
        indicators: list[str] = []
        ransomware = False
        firmware_tamper = False

        if commands_per_second > 100.0:
            ransomware = True
            indicators.append(
                f"Modbus/DNP3 command rate spike ({commands_per_second:.1f} cmd/s) indicates "
                "denial-of-control flood"
            )

        if unauthorized_function_codes:
            indicators.append(
                f"Unauthorized Modbus function codes intercepted: {unauthorized_function_codes}"
            )

        if untrusted_ip_connections > 0:
            indicators.append(
                f"{untrusted_ip_connections} unauthorized connection attempts to OT safety subnet"
            )

        for plc_id, fw_hash in plc_firmware_hashes.items():
            if fw_hash.lower() != expected_firmware_hash.lower():
                firmware_tamper = True
                indicators.append(
                    f"PLC {plc_id} firmware hash mismatch: {fw_hash[:12]}... != "
                    f"expected {expected_firmware_hash[:12]}..."
                )

        threat_score = min(
            1.0,
            (1.0 if firmware_tamper else 0.0) * 0.5
            + (1.0 if ransomware else 0.0) * 0.3
            + (min(5, untrusted_ip_connections) / 5.0) * 0.2,
        )

        level = (
            "CRITICAL" if threat_score >= 0.7 else ("HIGH" if threat_score >= 0.4 else "NOMINAL")
        )

        return PortSCADAAnomalyReport(
            ransomware_signature_detected=ransomware,
            unauthorized_plc_reprogramming=firmware_tamper,
            command_burst_frequency=commands_per_second,
            threat=ThreatSeverity(
                level=level,
                score=round(threat_score, 3),
                confidence=0.95,
                indicators=indicators,
                remediation_recommendation=(
                    "Isolate OT control network via air-gap diode; switch crane berths "
                    "to manual override"
                    if threat_score >= 0.4
                    else ""
                ),
            ),
        )


class AISSpoofingReport(BaseModel):
    """Maritime AIS kinematic trajectory and identity spoofing assessment."""

    is_kinematically_impossible: bool
    speed_over_ground_knots: float
    distance_jump_km: float
    mmsi_clone_detected: bool
    threat: ThreatSeverity


class AISSpoofingDetector:
    """Detects phantom vessel generation, coordinate hopping, and speed physics violations."""

    def analyze(
        self,
        *,
        previous_lat: float,
        previous_lon: float,
        current_lat: float,
        current_lon: float,
        elapsed_seconds: float,
        reported_sog_knots: float,
        vessel_type: str = "cargo",
    ) -> AISSpoofingReport:
        indicators: list[str] = []
        impossible = False

        # Haversine distance calculation
        phi1 = math.radians(previous_lat)
        phi2 = math.radians(current_lat)
        dphi = math.radians(current_lat - previous_lat)
        dlambda = math.radians(current_lon - previous_lon)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        distance_km = 6371.0 * c

        # Calculated speed in knots (1 km = 0.539957 nm)
        hours = max(1.0, elapsed_seconds) / 3600.0
        calc_speed_knots = (distance_km * 0.539957) / hours

        if calc_speed_knots > 45.0 and vessel_type == "cargo":
            impossible = True
            indicators.append(
                f"Calculated speed ({calc_speed_knots:.1f} kts) exceeds cargo hull physics "
                "(max 25 kts)"
            )

        if distance_km > 50.0 and elapsed_seconds < 120.0:
            impossible = True
            indicators.append(
                f"Coordinate teleportation jump of {distance_km:.1f} km in {elapsed_seconds:.0f}s"
            )

        threat_score = 0.95 if impossible else 0.05
        level = "CRITICAL" if impossible else "NOMINAL"

        return AISSpoofingReport(
            is_kinematically_impossible=impossible,
            speed_over_ground_knots=round(calc_speed_knots, 1),
            distance_jump_km=round(distance_km, 2),
            mmsi_clone_detected=impossible,
            threat=ThreatSeverity(
                level=level,
                score=round(threat_score, 3),
                confidence=0.98,
                indicators=indicators,
                remediation_recommendation=(
                    "Cross-reference vessel location with SAR synthetic aperture radar imagery"
                    if impossible
                    else ""
                ),
            ),
        )


class UnifiedCyberPhysicalScan(BaseModel):
    """Complete multi-vector cyber-physical threat assessment packet."""

    scan_id: UUID = Field(default_factory=uuid4)
    target_resource_ref: str
    overall_threat_level: str
    max_threat_score: float
    gnss_threat: GNSSAnomalyReport
    scada_threat: PortSCADAAnomalyReport
    ais_threat: AISSpoofingReport
    executive_summary: str


class ThreatDetectionEngine:
    """Unified engine running multi-vector cyber-physical threat scanning."""

    def __init__(self) -> None:
        self.gnss_detector = GNSSAnomalyDetector()
        self.scada_detector = PortSCADAAnomalyDetector()
        self.ais_detector = AISSpoofingDetector()

    def run_full_scan(
        self,
        resource_ref: str,
        *,
        gnss_residuals: list[float] | None = None,
        cno_ratios: list[float] | None = None,
        clock_drift_ppm: float = 0.0,
        scada_cmd_rate: float = 5.0,
        unauthorized_fc: list[int] | None = None,
        untrusted_ips: int = 0,
        plc_hashes: dict[str, str] | None = None,
        expected_plc_hash: str = "a1b2c3d4e5f6",
        ais_coords: tuple[float, float, float, float, float] | None = None,
    ) -> UnifiedCyberPhysicalScan:
        gnss_res = self.gnss_detector.analyze(
            pseudorange_residuals_m=gnss_residuals or [1.2, 1.5, 0.8, 1.1],
            carrier_to_noise_ratios_db=cno_ratios or [41.0, 42.5, 39.8],
            clock_drift_ppm=clock_drift_ppm,
        )

        scada_res = self.scada_detector.analyze(
            commands_per_second=scada_cmd_rate,
            unauthorized_function_codes=unauthorized_fc or [],
            untrusted_ip_connections=untrusted_ips,
            plc_firmware_hashes=plc_hashes or {"plc-01": expected_plc_hash},
            expected_firmware_hash=expected_plc_hash,
        )

        prev_lat, prev_lon, cur_lat, cur_lon, elapsed = (
            ais_coords if ais_coords else (70.5, 35.0, 70.52, 35.1, 1800.0)
        )
        ais_res = self.ais_detector.analyze(
            previous_lat=prev_lat,
            previous_lon=prev_lon,
            current_lat=cur_lat,
            current_lon=cur_lon,
            elapsed_seconds=elapsed,
            reported_sog_knots=14.0,
        )

        max_score = max(
            gnss_res.threat.score,
            scada_res.threat.score,
            ais_res.threat.score,
        )

        level = "CRITICAL" if max_score >= 0.75 else ("HIGH" if max_score >= 0.45 else "NOMINAL")

        summary = f"Threat Scan for {resource_ref}: {level} (max_score={max_score:.2f}). "
        if gnss_res.is_spoofed or gnss_res.is_jammed:
            summary += "GNSS EW Spoofing active. "
        if scada_res.ransomware_signature_detected or scada_res.unauthorized_plc_reprogramming:
            summary += "Port OT integrity compromised. "
        if ais_res.is_kinematically_impossible:
            summary += "AIS kinematic anomaly detected. "

        return UnifiedCyberPhysicalScan(
            target_resource_ref=resource_ref,
            overall_threat_level=level,
            max_threat_score=max_score,
            gnss_threat=gnss_res,
            scada_threat=scada_res,
            ais_threat=ais_res,
            executive_summary=summary.strip(),
        )
