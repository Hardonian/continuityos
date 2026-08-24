"""Canadian Geographic, Environmental, Permafrost, and Subsea Infrastructure Engine.

Provides:
  1. PermafrostDegradationModel: Active-layer thaw depth simulation and embankment settlement risk
     for Arctic rail corridors (Hudson Bay Railway) and northern highways (Dempster Highway).
  2. WildfireCorridorRiskModel: Canadian Fire Weather Index (FWI) fusion and corridor flame impingement
     modeling for Trans-Canada rail and highway links.
  3. SubseaAcousticMonitor: Subsea telecom cable and seabed energy conduit integrity monitoring.
  4. MountainPassGeomorphology: Rockfall, landslide, and avalanche hazard modeling for mountain corridors.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class TrackStabilityStatus(StrEnum):
    STABLE_FULL_SPEED = "stable_full_speed"
    SPEED_RESTRICTED = "speed_restricted"  # Slow order e.g. 10-15 mph
    CRITICAL_SETTLEMENT_SUSPENSION = "critical_settlement_suspension"


class PermafrostThawAssessment(BaseModel):
    """Assessment of permafrost degradation, thaw depth, and railway settlement."""

    assessment_id: UUID = Field(default_factory=uuid4)
    corridor_id: str
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    degree_days_of_thaw: float = Field(..., ge=0.0)
    calculated_thaw_depth_cm: float = Field(..., ge=0.0)
    settlement_risk_score: Score
    stability_status: TrackStabilityStatus
    recommended_max_speed_mph: int
    mitigation_action: str


class PermafrostDegradationModel:
    """Simulates active-layer thaw and trackbed differential settlement over discontinuous permafrost."""

    def evaluate_corridor_thaw(
        self,
        *,
        corridor_id: str,
        degree_days_of_thaw: float,
        soil_thermal_conductivity_w_mk: float = 1.4,
        latent_heat_mj_m3: float = 180.0,
        unfrozen_moisture_content: float = 0.28,
        insulating_peat_cover_cm: float = 15.0,
    ) -> PermafrostThawAssessment:
        # Modified Stefan solution for active-layer thaw depth in permafrost soils
        # Thaw depth d ≈ sqrt((2 * k * DDT * 86400) / L) adjusted for insulating organic peat cover
        time_seconds = degree_days_of_thaw * 86400.0
        latent_heat_joules = latent_heat_mj_m3 * 1_000_000.0

        raw_depth_m = math.sqrt((2.0 * soil_thermal_conductivity_w_mk * time_seconds) / latent_heat_joules)
        raw_depth_cm = raw_depth_m * 100.0

        # Organic insulation buffer dampens thaw penetration
        effective_thaw_cm = max(0.0, raw_depth_cm - (insulating_peat_cover_cm * 0.45))

        # Risk curve: >80cm thaw in peat/clay subgrade induces high differential settlement
        settlement_risk = min(1.0, effective_thaw_cm / 120.0)

        if settlement_risk > 0.75:
            status = TrackStabilityStatus.CRITICAL_SETTLEMENT_SUSPENSION
            max_speed = 0
            action = "Suspend heavy axle-load rail traffic; dispatch ballast tamping & ground radar inspection crew"
        elif settlement_risk > 0.40:
            status = TrackStabilityStatus.SPEED_RESTRICTED
            max_speed = 15
            action = "Enforce 15 mph slow order across thaw-sensitive subgrade zones; monitor thermosiphons"
        else:
            status = TrackStabilityStatus.STABLE_FULL_SPEED
            max_speed = 45
            action = "Nominal embankment conditions; continue routine geometric car telemetry logging"

        return PermafrostThawAssessment(
            corridor_id=corridor_id,
            degree_days_of_thaw=round(degree_days_of_thaw, 1),
            calculated_thaw_depth_cm=round(effective_thaw_cm, 1),
            settlement_risk_score=round(settlement_risk, 3),
            stability_status=status,
            recommended_max_speed_mph=max_speed,
            mitigation_action=action,
        )


class WildfireCorridorAssessment(BaseModel):
    """Fuses Canadian Fire Weather Index and active fire perimeter proximity."""

    corridor_id: str
    fire_weather_index_fwi: float = Field(..., ge=0.0)
    closest_fire_front_km: float = Field(..., ge=0.0)
    corridor_closure_probability: Score
    visibility_reduction_percent: float = Field(..., ge=0.0, le=100.0)
    operational_recommendation: str


class WildfireCorridorRiskModel:
    """Evaluates wildfire impingement risk and heavy smoke visibility loss on transport corridors."""

    def evaluate_wildfire_risk(
        self,
        *,
        corridor_id: str,
        fwi: float,
        closest_fire_distance_km: float,
        wind_speed_kmh: float = 25.0,
        wind_direction_towards_corridor: bool = True,
    ) -> WildfireCorridorAssessment:
        # FWI > 30 is Extreme in Canadian Forest Fire Danger Rating System (CFFDRS)
        fwi_factor = min(1.0, fwi / 40.0)

        # Proximity factor: < 10km is high threat
        proximity_factor = max(0.0, 1.0 - (closest_fire_distance_km / 30.0))

        wind_multiplier = 1.3 if (wind_direction_towards_corridor and wind_speed_kmh > 20.0) else 0.8
        closure_prob = min(1.0, (fwi_factor * 0.4 + proximity_factor * 0.6) * wind_multiplier)

        # Smoke visibility reduction model
        visibility_loss = min(95.0, (fwi_factor * 30.0) + (proximity_factor * 60.0))

        if closure_prob > 0.70:
            rec = "CRITICAL: Implement precautionary corridor shutdown and initiate modal rail/road bypass"
        elif closure_prob > 0.35:
            rec = "ELEVATED: Station water tender support units and enforce thermal sensor speed limits"
        else:
            rec = "LOW: Corridor clear; monitor ECCC FireSmoke and Canadian Wildland Fire Information System"

        return WildfireCorridorAssessment(
            corridor_id=corridor_id,
            fire_weather_index_fwi=round(fwi, 1),
            closest_fire_front_km=round(closest_fire_distance_km, 1),
            corridor_closure_probability=round(closure_prob, 3),
            visibility_reduction_percent=round(visibility_loss, 1),
            operational_recommendation=rec,
        )


class SubseaCableIntegrityAssessment(BaseModel):
    """Subsea telecom cable and pipeline anchor-drag / acoustic hazard evaluation."""

    infrastructure_id: str
    acoustic_anomaly_level: Score
    closest_unauthorized_anchoring_km: float
    integrity_score: Score
    choke_point_status: str
    defense_recommendation: str


class SubseaAcousticMonitor:
    """Monitors transatlantic subsea fiber and seabed energy pipeline security."""

    def evaluate_subsea_risk(
        self,
        *,
        infrastructure_id: str,
        acoustic_anomaly_db: float,
        closest_anchoring_vessel_dist_km: float,
        seabed_sensor_health: float = 0.95,
    ) -> SubseaCableIntegrityAssessment:
        # Acoustic anomaly > 15 dB above ambient baseline indicates seafloor disturbance
        acoustic_score = min(1.0, max(0.0, (acoustic_anomaly_db - 5.0) / 25.0))

        anchor_risk = max(0.0, 1.0 - (closest_anchoring_vessel_dist_km / 10.0))

        composite_risk = min(1.0, (acoustic_score * 0.55 + anchor_risk * 0.45) * (1.0 / seabed_sensor_health))
        integrity = max(0.0, 1.0 - composite_risk)

        if composite_risk > 0.65:
            status = "HIGH_THREAT_ANOMALY"
            rec = "Deploy Canadian Maritime Coastal Patrol / RCAF CP-140 Aurora for seabed inspection"
        elif composite_risk > 0.30:
            status = "SUSPICIOUS_SEABED_ACTIVITY"
            rec = "Alert Canadian Coast Guard MCTS to challenge vessel anchoring in cable protection zone"
        else:
            status = "NOMINAL_SEABED_INTEGRITY"
            rec = "Normal acoustic background levels across seabed cable corridor"

        return SubseaCableIntegrityAssessment(
            infrastructure_id=infrastructure_id,
            acoustic_anomaly_level=round(acoustic_score, 3),
            closest_unauthorized_anchoring_km=round(closest_anchoring_vessel_dist_km, 2),
            integrity_score=round(integrity, 3),
            choke_point_status=status,
            defense_recommendation=rec,
        )
