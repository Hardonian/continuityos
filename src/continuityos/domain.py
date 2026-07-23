from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Score = Annotated[float, Field(ge=0.0, le=1.0)]
Latitude = Annotated[float, Field(ge=-90.0, le=90.0)]
Longitude = Annotated[float, Field(ge=-180.0, le=180.0)]


class SourceTrust(StrEnum):
    AUTHORITATIVE_PUBLIC = "authoritative_public"
    OPEN_CONTEXT = "open_context"
    AUTHENTICATED_OPERATOR = "authenticated_operator"
    ANALYST_ASSESSMENT = "analyst_assessment"


class AssertionClass(StrEnum):
    GEOLOCATION = "geolocation"
    CLIMATE = "climate"
    ICE = "ice"
    WEATHER = "weather"
    EARTH_OBSERVATION = "earth_observation"
    ORBITAL_GEOMETRY = "orbital_geometry"
    TRAFFIC_HISTORY = "traffic_history"
    TRADE_EXPOSURE = "trade_exposure"
    POLICY_CONTEXT = "policy_context"
    GEOPOLITICAL_CONTEXT = "geopolitical_context"
    LIVE_CAPACITY = "live_capacity"
    LIVE_AVAILABILITY = "live_availability"
    CYBER_HEALTH = "cyber_health"
    INSURANCE_ACCESS = "insurance_access"
    HUMAN_INTELLIGENCE = "human_intelligence"


class MetricName(StrEnum):
    SEA_ICE_CONCENTRATION = "sea_ice_concentration"
    SEA_ICE_EXTENT_ANOMALY = "sea_ice_extent_anomaly"
    EARTH_OBSERVATION_COVERAGE = "earth_observation_coverage"
    WIND_SEVERITY = "wind_severity"
    WAVE_SEVERITY = "wave_severity"
    PORT_GEOMETRY = "port_geometry"
    PORT_CAPACITY = "port_capacity"
    PORT_AVAILABILITY = "port_availability"
    AIS_TRAFFIC_INDEX = "ais_traffic_index"
    TRADE_DEPENDENCY = "trade_dependency"
    SATELLITE_GEOMETRY_DENSITY = "satellite_geometry_density"
    SATCOM_AVAILABILITY = "satcom_availability"
    CYBER_CONTROL_HEALTH = "cyber_control_health"
    DATA_INTEGRITY = "data_integrity"
    INSURANCE_AVAILABILITY = "insurance_availability"
    GEOPOLITICAL_PRESSURE = "geopolitical_pressure"
    ESCORT_CAPACITY = "escort_capacity"
    INVENTORY_DAYS = "inventory_days"


class GeoPoint(BaseModel):
    model_config = ConfigDict(frozen=True)
    latitude: Latitude
    longitude: Longitude


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)
    uri: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_id: str | None = None
    licence: str | None = None


class Observation(BaseModel):
    model_config = ConfigDict(frozen=True)
    observation_id: UUID = Field(default_factory=uuid4)
    source_id: str = Field(min_length=2, max_length=128)
    source_trust: SourceTrust
    assertion_class: AssertionClass
    metric: MetricName
    value: float
    unit: str = Field(min_length=1, max_length=32)
    observed_at: datetime
    valid_until: datetime | None = None
    location: GeoPoint | None = None
    confidence: Score
    provenance: Provenance
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observed_at", "valid_until")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_metric_value(self) -> Observation:
        if not math.isfinite(self.value):
            raise ValueError("observation value must be finite")
        ratio_metrics = {
            MetricName.WIND_SEVERITY,
            MetricName.WAVE_SEVERITY,
            MetricName.PORT_CAPACITY,
            MetricName.PORT_AVAILABILITY,
            MetricName.AIS_TRAFFIC_INDEX,
            MetricName.TRADE_DEPENDENCY,
            MetricName.SATCOM_AVAILABILITY,
            MetricName.CYBER_CONTROL_HEALTH,
            MetricName.DATA_INTEGRITY,
            MetricName.INSURANCE_AVAILABILITY,
            MetricName.GEOPOLITICAL_PRESSURE,
            MetricName.ESCORT_CAPACITY,
        }
        if self.metric in ratio_metrics and not 0.0 <= self.value <= 1.0:
            raise ValueError(f"{self.metric} must be normalized to [0, 1]")
        if self.metric == MetricName.SEA_ICE_CONCENTRATION:
            upper = 100.0 if self.unit.lower() in {"percent", "%"} else 1.0
            if not 0.0 <= self.value <= upper:
                raise ValueError(f"sea-ice concentration outside [0, {upper:g}]")
        if self.metric == MetricName.INVENTORY_DAYS and not 0.0 <= self.value <= 3650.0:
            raise ValueError("inventory_days outside supported range")
        if (
            self.metric
            in {
                MetricName.SATELLITE_GEOMETRY_DENSITY,
                MetricName.EARTH_OBSERVATION_COVERAGE,
                MetricName.PORT_GEOMETRY,
            }
            and self.value < 0
        ):
            raise ValueError(f"{self.metric} cannot be negative")
        if self.valid_until is not None and self.valid_until < self.observed_at:
            raise ValueError("valid_until cannot precede observed_at")
        return self


class CorridorFactor(StrEnum):
    ICE = "ice"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    PORT = "port"
    COMMUNICATIONS = "communications"
    CYBER = "cyber"
    DATA_TRUST = "data_trust"
    COMMERCIAL = "commercial"
    GEOPOLITICAL = "geopolitical"
    ESCORT = "escort"
    INVENTORY = "inventory"


class FactorAssessment(BaseModel):
    factor: CorridorFactor
    risk: Score
    confidence: Score
    evidence_ids: list[UUID]
    rationale: str


class CorridorState(StrEnum):
    OPEN = "open"
    DEGRADED = "degraded"
    FUNCTIONALLY_CLOSED = "functionally_closed"
    PHYSICALLY_CLOSED = "physically_closed"


class CorridorAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    corridor_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_risk: Score
    confidence: Score
    state: CorridorState
    factors: list[FactorAssessment]
    missing_required_metrics: list[MetricName]
    caveats: list[str]


class ContinuityObjective(BaseModel):
    minimum_continuity: Score = 0.95
    maximum_shortage_days: int = Field(default=7, ge=0, le=365)
    maximum_recovery_days: int = Field(default=45, ge=1, le=730)
    budget: float = Field(gt=0)
    human_approval_required: bool = True


class MitigationAction(BaseModel):
    action_id: str
    name: str
    cost: float = Field(ge=0)
    continuity_gain: Score
    risk_reductions: dict[CorridorFactor, Score] = Field(default_factory=dict)
    prerequisites: set[str] = Field(default_factory=set)
    incompatible_with: set[str] = Field(default_factory=set)
    lead_time_hours: int = Field(default=0, ge=0)
    requires_human_approval: bool = True
    rationale: str


class CompileRequest(BaseModel):
    assessment: CorridorAssessment
    objective: ContinuityObjective
    available_actions: list[MitigationAction]


class CompiledPlan(BaseModel):
    plan_id: UUID = Field(default_factory=uuid4)
    assessment_id: UUID
    selected_actions: list[MitigationAction]
    total_cost: float
    projected_continuity: Score
    projected_risk: Score
    objective_met: bool
    deterministic_solver: str
    approval_required: bool
    rejected_reason: str | None = None
