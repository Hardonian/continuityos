"""Sovereign Counter-Intelligence, Anti-Reconnaissance, and Maritime Surveillance Engine.

Provides defensive capabilities:
  1. DarkFleetDetector: Correlates optical/radar maritime contacts against active AIS broadcasts
     to identify non-transmitting (dark) vessels, MMSI spoofing, and covert loitering near EEZ boundaries.
  2. SARSatelliteOverflightPredictor: Models foreign Earth Observation / SAR satellite overflight
     exposure windows over strategic defense corridors, critical mineral convoys, and naval bases.
  3. EMCONPostureManager: Evaluates emission control posture (Alpha/Bravo/Charlie) and RF signature
     leakage for secure resupply operations.
  4. InsiderReconDetector: Detects anomalous geographic telemetry scraping and reconnaissance patterns.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import GeoPoint, Score


class EMCONLevel(StrEnum):
    ALPHA_SILENT = "alpha_silent"  # Complete RF emission silence
    BRAVO_LOW_PROBABILITY = "bravo_low_probability"  # Directional LPI/LPD communications only
    CHARLIE_ACTIVE = "charlie_active"  # Standard active transmissions permitted


class DarkVesselContact(BaseModel):
    """Correlated maritime contact exhibiting anomalous surveillance signatures."""

    contact_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    estimated_speed_knots: float = Field(..., ge=0.0)
    estimated_length_meters: float = Field(default=100.0, ge=0.0)
    ais_active: bool = False
    spoofed_mmsi: str | None = None
    proximity_to_critical_asset_km: float = Field(..., ge=0.0)
    threat_level: Score = 0.5
    anomaly_flags: list[str] = Field(default_factory=list)


class DarkFleetAssessment(BaseModel):
    """Aggregate evaluation of dark fleet activity and covert maritime presence."""

    assessment_id: UUID = Field(default_factory=uuid4)
    corridor_id: str
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_contacts_detected: int
    dark_vessels_count: int
    highest_threat_score: Score
    contacts: list[DarkVesselContact]
    surveillance_advisory: str


class DarkFleetDetector:
    """Detects and scores non-transmitting vessels and AIS spoofing in sovereign maritime zones."""

    def correlate_contacts(
        self,
        *,
        corridor_id: str,
        radar_optical_contacts: list[dict[str, Any]],
        active_ais_mmsis: set[str],
        asset_location: GeoPoint,
    ) -> DarkFleetAssessment:
        contacts: list[DarkVesselContact] = []
        max_threat: float = 0.0

        for idx, contact in enumerate(radar_optical_contacts):
            c_lat = float(contact.get("latitude", 0.0))
            c_lon = float(contact.get("longitude", 0.0))
            c_speed = float(contact.get("speed_knots", 0.0))
            c_len = float(contact.get("length_meters", 80.0))
            reported_mmsi = contact.get("mmsi")

            # Calculate distance to asset using haversine formula
            dist_km = self._haversine_km(
                asset_location.latitude, asset_location.longitude, c_lat, c_lon
            )

            is_dark = reported_mmsi is None or str(reported_mmsi) not in active_ais_mmsis
            flags: list[str] = []
            threat = 0.2

            if is_dark:
                threat += 0.4
                flags.append("AIS_TRANSPONDER_INACTIVE_OR_DARK")

            if dist_km < 25.0:
                threat += 0.25
                flags.append(f"CRITICAL_PROXIMITY_{dist_km:.1f}KM")

            if c_speed < 2.0 and dist_km < 50.0:
                threat += 0.15
                flags.append("SUSPICIOUS_CHOKEPOINT_LOITERING")

            threat_score = min(1.0, threat)
            max_threat = max(max_threat, threat_score)

            contacts.append(
                DarkVesselContact(
                    contact_id=f"CONTACT-RADAR-{idx + 1:03d}",
                    latitude=c_lat,
                    longitude=c_lon,
                    estimated_speed_knots=c_speed,
                    estimated_length_meters=c_len,
                    ais_active=not is_dark,
                    spoofed_mmsi=str(reported_mmsi) if reported_mmsi and is_dark else None,
                    proximity_to_critical_asset_km=round(dist_km, 2),
                    threat_level=round(threat_score, 3),
                    anomaly_flags=flags,
                )
            )

        dark_count = sum(1 for c in contacts if not c.ais_active)
        advisory = (
            f"Detected {dark_count} dark/unverified contacts within sensor range. "
            f"Highest contact threat score: {max_threat:.2f}."
        )

        return DarkFleetAssessment(
            corridor_id=corridor_id,
            total_contacts_detected=len(contacts),
            dark_vessels_count=dark_count,
            highest_threat_score=round(max_threat, 3),
            contacts=contacts,
            surveillance_advisory=advisory,
        )

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0  # Earth mean radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c


class OverflightPass(BaseModel):
    """Predictive orbital Earth Observation or SAR pass over target coordinates."""

    satellite_id: str
    sensor_type: str  # "SAR_RADAR", "OPTICAL_HIGH_RES", "SIGINT_ELINT"
    pass_start: datetime
    pass_end: datetime
    elevation_angle_max_deg: float
    exposure_vulnerability_score: Score
    masking_recommendation: str


class OverflightExposureReport(BaseModel):
    """Evaluation of orbital surveillance overflight exposure over a strategic corridor."""

    corridor_id: str
    total_passes_projected: int
    peak_vulnerability_index: Score
    passes: list[OverflightPass]
    recommended_emcon_level: EMCONLevel
    tactical_directive: str


class SARSatelliteOverflightPredictor:
    """Predicts foreign orbital Earth Observation & SAR reconnaissance passes."""

    def evaluate_exposure(
        self,
        *,
        corridor_id: str,
        orbital_ephemeris: list[dict[str, Any]],
        critical_corridor_length_km: float = 100.0,
    ) -> OverflightExposureReport:
        passes: list[OverflightPass] = []
        max_vuln: float = 0.0

        for eph in orbital_ephemeris:
            sat_id = str(eph.get("satellite_id", "UNKNOWN-SAT"))
            sensor = str(eph.get("sensor_type", "SAR_RADAR"))
            elev = float(eph.get("elevation_max_deg", 45.0))
            duration_mins = float(eph.get("duration_minutes", 12.0))

            # Higher elevation angles produce higher resolution radar & optical imaging
            elev_factor = min(1.0, elev / 90.0)
            sensor_weight = 1.0 if "SAR" in sensor.upper() else 0.8
            vuln = min(1.0, elev_factor * sensor_weight)
            max_vuln = max(max_vuln, vuln)

            masking = (
                "Execute RF emissions cutoff & scatter decoy transponders during pass window"
                if vuln > 0.6
                else "Maintain standard low-power directional communications"
            )

            now = datetime.now(UTC)
            passes.append(
                OverflightPass(
                    satellite_id=sat_id,
                    sensor_type=sensor,
                    pass_start=now,
                    pass_end=now,
                    elevation_angle_max_deg=elev,
                    exposure_vulnerability_score=round(vuln, 3),
                    masking_recommendation=masking,
                )
            )

        emcon = (
            EMCONLevel.ALPHA_SILENT
            if max_vuln > 0.75
            else (EMCONLevel.BRAVO_LOW_PROBABILITY if max_vuln > 0.40 else EMCONLevel.CHARLIE_ACTIVE)
        )

        directive = (
            f"Orbital reconnaissance risk index: {max_vuln:.2f}. "
            f"Recommended operational posture: {emcon.value.upper()}."
        )

        return OverflightExposureReport(
            corridor_id=corridor_id,
            total_passes_projected=len(passes),
            peak_vulnerability_index=round(max_vuln, 3),
            passes=passes,
            recommended_emcon_level=emcon,
            tactical_directive=directive,
        )


class InsiderReconDetector:
    """Detects suspicious access patterns, boundary scraping, and covert reconnaissance."""

    def evaluate_query_telemetry(
        self,
        *,
        operator_id: str,
        query_count_last_hour: int,
        geographic_bounding_boxes_scraped: int,
        attempted_clearance_escalations: int = 0,
    ) -> dict[str, Any]:
        risk = 0.1
        flags: list[str] = []

        if query_count_last_hour > 500:
            risk += 0.35
            flags.append("HIGH_FREQUENCY_BULK_TELEMETRY_SCRAPING")

        if geographic_bounding_boxes_scraped > 20:
            risk += 0.30
            flags.append("WIDE_AREA_GEOGRAPHIC_RECONNAISSANCE")

        if attempted_clearance_escalations > 0:
            risk += 0.40
            flags.append(f"UNAUTHORIZED_CLEARANCE_ESCALATION_ATTEMPTS_{attempted_clearance_escalations}")

        risk_score = min(1.0, risk)
        is_threat = risk_score > 0.65

        return {
            "operator_id": operator_id,
            "counter_intel_threat_score": round(risk_score, 3),
            "is_anomaly_threat": is_threat,
            "anomaly_flags": flags,
            "counter_measure": (
                "Isolate session, enforce rate limiting, and alert sovereign security officer"
                if is_threat
                else "Nominal activity logged"
            ),
        }
