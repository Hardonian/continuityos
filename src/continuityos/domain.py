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
    DISASTER_RESPONSE = "disaster_response"
    TACTICAL_SURVEILLANCE = "tactical_surveillance"
    COUNTER_UAS = "counter_uas"
    LEO_SATCOM = "leo_satcom"
    SUPPLY_CHAIN_INTELLIGENCE = "supply_chain_intelligence"
    STRATEGIC_MINERALS = "strategic_minerals"
    RAIL_LOGISTICS = "rail_logistics"
    COUNTER_INTELLIGENCE = "counter_intelligence"
    PERMAFROST_INTEGRITY = "permafrost_integrity"
    WILDFIRE_THREAT = "wildfire_threat"
    SUBSEA_INFRASTRUCTURE = "subsea_infrastructure"
    EMCON_SURVEILLANCE = "emcon_surveillance"


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
    WEATHER_ALERT_ACTIVITY = "weather_alert_activity"
    DISASTER_EVENT_ACTIVITY = "disaster_event_activity"
    CASUALTY_COUNT = "casualty_count"
    INJURED_COUNT = "injured_count"
    EVACUATION_COUNT = "evacuation_count"
    UTILITY_IMPACT_COUNT = "utility_impact_count"
    WATER_LEVEL = "water_level"
    UAV_LINK_MARGIN = "uav_link_margin"
    UAV_SWARM_COHESION = "uav_swarm_cohesion"
    STARLINK_LATENCY_MS = "starlink_latency_ms"
    STARLINK_DOWNLINK_MBPS = "starlink_downlink_mbps"
    STARLINK_OBSTRUCTION_RATE = "starlink_obstruction_rate"
    CUAS_THREAT_DENSITY = "cuas_threat_density"
    CUAS_JAMMING_ACTIVE = "cuas_jamming_active"
    RAIL_NETWORK_FLUIDITY = "rail_network_fluidity"
    MINERAL_RESERVE_DAYS = "mineral_reserve_days"
    REFINERY_CAPACITY_UTILIZATION = "refinery_capacity_utilization"
    BORDER_CROSSING_DELAY_HOURS = "border_crossing_delay_hours"
    DEMURRAGE_RISK_INDEX = "demurrage_risk_index"
    LOCK_OPERATIONAL_STATUS = "lock_operational_status"
    PERMAFROST_THAW_DEPTH_CM = "permafrost_thaw_depth_cm"
    WILDFIRE_INDEX_FWI = "wildfire_index_fwi"
    DARK_VESSEL_PROXIMITY_KM = "dark_vessel_proximity_km"
    SAR_SATELLITE_EXPOSURE_INDEX = "sar_satellite_exposure_index"
    ACOUSTIC_ANOMALY_LEVEL = "acoustic_anomaly_level"
    SEABED_CABLE_INTEGRITY = "seabed_cable_integrity"
    EMCON_COMPLIANCE_SCORE = "emcon_compliance_score"


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
            MetricName.UAV_SWARM_COHESION,
            MetricName.STARLINK_OBSTRUCTION_RATE,
            MetricName.CUAS_THREAT_DENSITY,
            MetricName.CUAS_JAMMING_ACTIVE,
            MetricName.RAIL_NETWORK_FLUIDITY,
            MetricName.REFINERY_CAPACITY_UTILIZATION,
            MetricName.DEMURRAGE_RISK_INDEX,
            MetricName.LOCK_OPERATIONAL_STATUS,
            MetricName.SAR_SATELLITE_EXPOSURE_INDEX,
            MetricName.ACOUSTIC_ANOMALY_LEVEL,
            MetricName.SEABED_CABLE_INTEGRITY,
            MetricName.EMCON_COMPLIANCE_SCORE,
        }
        if self.metric in ratio_metrics and not 0.0 <= self.value <= 1.0:
            raise ValueError(f"{self.metric} must be normalized to [0, 1]")
        if self.metric == MetricName.SEA_ICE_CONCENTRATION:
            upper = 100.0 if self.unit.lower() in {"percent", "%"} else 1.0
            if not 0.0 <= self.value <= upper:
                raise ValueError(f"sea-ice concentration outside [0, {upper:g}]")
        if (
            self.metric in {MetricName.INVENTORY_DAYS, MetricName.MINERAL_RESERVE_DAYS}
            and not 0.0 <= self.value <= 3650.0
        ):
            raise ValueError(f"{self.metric} outside supported range")
        if (
            self.metric
            in {
                MetricName.SATELLITE_GEOMETRY_DENSITY,
                MetricName.EARTH_OBSERVATION_COVERAGE,
                MetricName.PORT_GEOMETRY,
                MetricName.UAV_LINK_MARGIN,
                MetricName.STARLINK_LATENCY_MS,
                MetricName.STARLINK_DOWNLINK_MBPS,
                MetricName.BORDER_CROSSING_DELAY_HOURS,
                MetricName.PERMAFROST_THAW_DEPTH_CM,
                MetricName.WILDFIRE_INDEX_FWI,
                MetricName.DARK_VESSEL_PROXIMITY_KM,
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
    OPEN_DEGRADED = "open_degraded"
    OPEN_CAPACITY_CONSTRAINED = "open_capacity_constrained"
    OPEN_BUT_UNINSURABLE = "open_but_uninsurable"
    OPEN_BUT_NO_CARRIER_CAPACITY = "open_but_no_carrier_capacity"
    OPEN_BUT_NAVIGATION_UNTRUSTED = "open_but_navigation_untrusted"
    OPEN_BUT_COMMUNICATIONS_DEGRADED = "open_but_communications_degraded"
    OPEN_BUT_SERVICE_DEPENDENT = "open_but_service_dependent"
    RECOVERY_BACKLOGGED = "recovery_backlogged"
    FUNCTIONALLY_CLOSED = "functionally_closed"
    PHYSICALLY_CLOSED = "physically_closed"
    UNKNOWN = "unknown"
    # Legacy alias for backward compatibility with existing fusion tests
    DEGRADED = "open_degraded"

    @classmethod
    def from_str(cls, val: str | CorridorState) -> CorridorState:
        """Parse or normalize a string or CorridorState instance."""
        if isinstance(val, cls):
            return val
        s = str(val).lower()
        if s == "degraded":
            return cls.OPEN_DEGRADED
        for item in cls:
            if item.value == s:
                return item
        return cls.UNKNOWN


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


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    UNCLASSIFIED = "unclassified"
    PROTECTED_A = "protected_a"
    PROTECTED_B = "protected_b"
    PROTECTED_C = "protected_c"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"
    COSMIC_TOP_SECRET = "cosmic_top_secret"

    @property
    def level(self) -> int:
        """Numeric clearance level for comparison."""
        levels = {
            self.PUBLIC: 0,
            self.UNCLASSIFIED: 0,
            self.INTERNAL: 1,
            self.PROTECTED_A: 1,
            self.PROTECTED_B: 2,
            self.RESTRICTED: 2,
            self.PROTECTED_C: 3,
            self.CONFIDENTIAL: 3,
            self.SECRET: 4,
            self.TOP_SECRET: 5,
            self.COSMIC_TOP_SECRET: 6,
        }
        return levels.get(self, 0)


class RecoveryObjective(BaseModel):
    """Recovery time/point objectives for a resource or supply network."""

    recovery_time_hours: int = Field(ge=0, le=8760)
    recovery_point_hours: int = Field(ge=0, le=8760)
    minimum_service_level: Score = 0.5
    maximum_data_loss_hours: int = Field(default=24, ge=0, le=8760)
    priority: int = Field(default=1, ge=1, le=5)


# --- Composable Corridor State Dimensions ---


class PhysicalStateEnum(StrEnum):
    OPEN = "open"
    CAPACITY_CONSTRAINED = "capacity_constrained"
    PHYSICALLY_CLOSED = "physically_closed"
    UNKNOWN = "unknown"


class OperationalState(BaseModel):
    navigation: str = "healthy"  # healthy, degraded, untrusted, unavailable
    communications: str = "healthy"  # healthy, degraded, unavailable
    escort_service: str = "available"  # available, unavailable, dependent
    weather_clearance: str = "clear"  # clear, degraded, severe


class CommercialState(BaseModel):
    carrier_capacity: str = "available"  # available, constrained, unavailable
    insurance: str = "available"  # available, uninsurable, withdrawn
    commercial_viability: Score = 1.0


class DigitalTrustState(BaseModel):
    navigation_integrity: Score = 1.0
    communications_integrity: Score = 1.0
    cyber_integrity: Score = 1.0
    data_integrity: Score = 1.0


class RecoveryStateEnum(StrEnum):
    NORMAL = "normal"
    INCIDENT_T0 = "incident_t0"
    PHYSICAL_REOPENED_T1 = "physical_reopened_t1"
    COMMERCIAL_NORMALIZED_T2 = "commercial_normalized_t2"
    LOGISTICS_NORMALIZED_T3 = "logistics_normalized_t3"
    INVENTORY_REPLENISHED_T4 = "inventory_replenished_t4"
    FULL_RESTORATION_T5 = "full_restoration_t5"
    BACKLOG_ACTIVE = "backlog_active"


class RecoveryState(BaseModel):
    phase: RecoveryStateEnum = RecoveryStateEnum.NORMAL
    backlog_active: bool = False
    days_elapsed: int = 0
    estimated_full_restoration_days: int = 0


class EffectiveCorridorState(BaseModel):
    physical_state: PhysicalStateEnum = PhysicalStateEnum.OPEN
    operational_state: OperationalState = Field(default_factory=OperationalState)
    commercial_state: CommercialState = Field(default_factory=CommercialState)
    digital_trust_state: DigitalTrustState = Field(default_factory=DigitalTrustState)
    recovery_state: RecoveryState = Field(default_factory=RecoveryState)
    effective_state: CorridorState = CorridorState.OPEN
    reason_codes: list[str] = Field(default_factory=list)


# --- Communication Tiers ---


class CommunicationTier(StrEnum):
    COMMERCIAL_LEO = "commercial_leo"
    GOVERNMENT_SATCOM = "government_satcom"
    PROTECTED_SATCOM = "protected_satcom"
    TERRESTRIAL_FALLBACK = "terrestrial_fallback"
    HF = "hf"
    VHF = "vhf"
    MESH = "mesh"
    STORE_AND_FORWARD = "store_and_forward"


# --- Drone, Sensor & Counter-Drone Representation (Defensive Only) ---


class UncrewedSystem(BaseModel):
    system_id: str
    name: str
    system_type: str = "UAS"  # UAS, USV, UUV, UGV
    coverage_radius_km: float = Field(default=50.0, ge=0.0)
    availability: Score = 1.0
    endurance_hours: float = Field(default=8.0, ge=0.0)
    communications_link: str = "secure_mesh"
    environmental_limits: dict[str, float] = Field(default_factory=dict)
    sensor_types: list[str] = Field(default_factory=lambda: ["EO_IR", "RF_SNIFFER"])
    confidence: Score = 0.9
    maintenance_state: str = "operational"


class SensorNode(BaseModel):
    node_id: str
    name: str
    modality: str  # RF, RADAR, EO_IR, ACOUSTIC, AIS, BUOY
    location: GeoPoint | None = None
    confidence: Score = 0.95
    status: str = "operational"


class RelayNode(BaseModel):
    relay_id: str
    name: str
    throughput_mbps: float = 100.0
    latency_ms: float = 25.0
    redundancy_level: int = 1


class ObservationPlatform(BaseModel):
    platform_id: str
    name: str
    platform_type: str  # ORBITAL_LEO, ORBITAL_GEO, HAPS, MARITIME_PATROL, SENSOR_BUOY
    sensors: list[str] = Field(default_factory=list)
    confidence: Score = 0.9


class CounterUASCoverage(BaseModel):
    coverage_id: str
    protected_area_id: str
    detection_radius_km: float = 10.0
    identification_confidence: Score = 0.95
    track_fusion_health: Score = 1.0
    authorization_state: str = "defensive_standby"  # defensive_standby, alert, authorized
    coverage_continuity: Score = 1.0


# --- Strategic Inventory Domain Model ---


class StrategicInventory(BaseModel):
    inventory_id: str
    name: str
    commodity: str  # FUEL, MEDICINE, CRITICAL_SPARES, GRAIN, MINERALS
    starting_quantity: float = Field(gt=0)
    unit: str = "liters"
    minimum_reserve_days: int = 30
    critical_reserve_days: int = 15
    normal_burn_rate: float = Field(gt=0)
    degraded_burn_rate: float | None = None
    emergency_burn_rate: float | None = None
    current_reserve_days: float = 0.0
    assured_replenishment_days: int = 0
    storage_constraints_capacity: float | None = None


# --- Assurance Policy & Route Substitution Models ---


class AssuranceObjectiveSpec(BaseModel):
    minimum: Score = 0.95


class AssuranceToleranceSpec(BaseModel):
    corridor_loss: int = 1
    port_loss: int = 1
    communication_provider_loss: int = 1
    navigation_source_loss: int = 2
    observation_source_loss: int = 1


class AssuranceEvidenceSpec(BaseModel):
    minimum_independent_operational_sources: int = 2
    minimum_independent_navigation_sources: int = 3
    minimum_independent_environmental_sources: int = 2


class AssuranceCommercialSpec(BaseModel):
    minimum_carrier_options: int = 2
    insurance_required: bool = True


class AssuranceInventorySpec(BaseModel):
    minimum_reserve_days: int = 30
    minimum_assured_replenishment_cycles: int = 1


class AssuranceRecoverySpec(BaseModel):
    verify_carrier_return: bool = True
    verify_backlog_clearance: bool = True
    verify_reserve_restoration: bool = True


class AssurancePolicy(BaseModel):
    policy_id: str
    name: str
    continuity_objective: AssuranceObjectiveSpec = Field(default_factory=AssuranceObjectiveSpec)
    tolerate: AssuranceToleranceSpec = Field(default_factory=AssuranceToleranceSpec)
    evidence: AssuranceEvidenceSpec = Field(default_factory=AssuranceEvidenceSpec)
    commercial: AssuranceCommercialSpec = Field(default_factory=AssuranceCommercialSpec)
    inventory: AssuranceInventorySpec = Field(default_factory=AssuranceInventorySpec)
    recovery: AssuranceRecoverySpec = Field(default_factory=AssuranceRecoverySpec)


class RouteSubstitution(BaseModel):
    substitution_id: str
    name: str
    primary_route_id: str
    alternative_route_id: str
    cargo_type: str
    quantity: float
    required_arrival_days: int
    vessel_class_required: str | None = None
    ice_class_required: bool = False
