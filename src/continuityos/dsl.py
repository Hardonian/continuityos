"""Declarative Continuity-as-Code resource system.

Provides YAML-based declarative specification for supply networks, policies,
dependency trust, and scenarios following the ``apiVersion: continuity.io/v1``
convention.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

from continuityos.domain import Score


class ResourceKind(StrEnum):
    SUPPLY_NETWORK = "SupplyNetwork"
    CORRIDOR = "Corridor"
    ROUTE = "Route"
    PORT = "Port"
    TERMINAL = "Terminal"
    CARRIER = "Carrier"
    VESSEL_CLASS = "VesselClass"
    ICEBREAKER_SERVICE = "IcebreakerService"
    INVENTORY = "Inventory"
    SUPPLIER = "Supplier"
    FACILITY = "Facility"
    COMMUNICATION_PROVIDER = "CommunicationProvider"
    NAVIGATION_SOURCE = "NavigationSource"
    OBSERVATION_SOURCE = "ObservationSource"
    DEPENDENCY = "Dependency"
    DEPENDENCY_TRUST = "DependencyTrust"
    CONTINUITY_POLICY = "ContinuityPolicy"
    SCENARIO = "Scenario"
    RECOVERY_OBJECTIVE = "RecoveryObjective"
    EVIDENCE = "Evidence"
    OBSERVATION = "Observation"
    REMEDIATION = "Remediation"
    ASSURANCE_POLICY = "AssurancePolicy"
    ROUTE_SUBSTITUTION = "RouteSubstitution"
    STRATEGIC_INVENTORY = "StrategicInventory"
    RECOVERY_STATE = "RecoveryState"
    UNCREWED_SYSTEM = "UncrewedSystem"
    SENSOR_NODE = "SensorNode"
    RELAY_NODE = "RelayNode"
    OBSERVATION_PLATFORM = "ObservationPlatform"
    COUNTER_UAS_COVERAGE = "CounterUASCoverage"


class ResourceMetadata(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    namespace: str = Field(default="default", min_length=1, max_length=128)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    owner: str | None = None
    created_at: datetime | None = None


# --- SupplyNetwork spec ---


class RedundancySpec(BaseModel):
    minimum_routes: int = Field(default=2, ge=1, le=100)
    minimum_ports: int = Field(default=2, ge=1, le=100)
    minimum_satcom_providers: int = Field(default=2, ge=1, le=20)
    minimum_navigation_sources: int = Field(default=3, ge=1, le=20)
    minimum_observation_sources: int = Field(default=2, ge=1, le=20)


class InventorySpec(BaseModel):
    fuel_reserve_days: int = Field(default=30, ge=0, le=3650)
    medical_reserve_days: int = Field(default=60, ge=0, le=3650)


class FailureToleranceSpec(BaseModel):
    routes_unavailable: int = Field(default=1, ge=0, le=50)
    ports_unavailable: int = Field(default=1, ge=0, le=50)
    communication_providers_unavailable: int = Field(default=1, ge=0, le=20)
    navigation_sources_untrusted: int = Field(default=2, ge=0, le=20)


class RecoverySpec(BaseModel):
    require_inventory_recovery_model: bool = True
    require_carrier_return_model: bool = True
    require_port_backlog_model: bool = True


class ObjectivesSpec(BaseModel):
    minimum_continuity: Score = 0.95
    maximum_critical_shortage_days: int = Field(default=7, ge=0, le=365)
    maximum_recovery_days: int = Field(default=30, ge=1, le=730)


class DependencyRulesSpec(BaseModel):
    prohibit_single_state_service_dependency: bool = True
    require_independent_navigation_sources: bool = True
    require_independent_observation_sources: bool = True


class SupplyNetworkSpec(BaseModel):
    objectives: ObjectivesSpec = Field(default_factory=ObjectivesSpec)
    redundancy: RedundancySpec = Field(default_factory=RedundancySpec)
    inventory: InventorySpec = Field(default_factory=InventorySpec)
    dependency_rules: DependencyRulesSpec = Field(default_factory=DependencyRulesSpec)
    failure_tolerance: FailureToleranceSpec = Field(default_factory=FailureToleranceSpec)
    recovery: RecoverySpec = Field(default_factory=RecoverySpec)


# --- DependencyTrust spec ---


class TrustDimensions(BaseModel):
    physical_availability: Score = 1.0
    cyber_integrity: Score = 1.0
    legal_availability: Score = 1.0
    commercial_availability: Score = 1.0
    insurance_availability: Score = 1.0
    communications_integrity: Score = 1.0
    navigation_integrity: Score = 1.0
    operator_confidence: Score = 1.0
    information_confidence: Score = 1.0


class TrustAggregation(StrEnum):
    MINIMUM = "minimum"
    WEIGHTED = "weighted"
    MEAN = "mean"


class TrustStrategySpec(BaseModel):
    aggregation: TrustAggregation = TrustAggregation.MINIMUM


class TrustProvenanceSpec(BaseModel):
    minimum_independent_sources: int = Field(default=2, ge=1, le=20)


class DependencyTrustSpec(BaseModel):
    dependency_ref: str = Field(min_length=1, max_length=256)
    dimensions: TrustDimensions = Field(default_factory=TrustDimensions)
    strategy: TrustStrategySpec = Field(default_factory=TrustStrategySpec)
    provenance: TrustProvenanceSpec = Field(default_factory=TrustProvenanceSpec)


# --- ContinuityPolicy spec ---


class PolicyAssertion(BaseModel):
    minimum_providers: int | None = None
    minimum_reserve_days: int | None = None
    minimum_independent_routes: int | None = None
    minimum_continuity: Score | None = None
    maximum_single_dependency_concentration: Score | None = None
    minimum_trust_score: Score | None = None


class PolicyRule(BaseModel):
    rule_id: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=512)
    assertion: PolicyAssertion


class ContinuityPolicySpec(BaseModel):
    rules: list[PolicyRule] = Field(min_length=1, max_length=500)


# --- Scenario spec ---


class ScenarioEvent(BaseModel):
    target: str = Field(min_length=1, max_length=256)
    state: str = Field(min_length=1, max_length=64)
    description: str | None = None


class ScenarioSpec(BaseModel):
    events: list[ScenarioEvent] = Field(default_factory=list, min_length=0, max_length=200)
    duration_days: int = Field(default=30, ge=1, le=3650)
    description: str | None = None


# --- AssurancePolicy spec ---


class AssuranceObjectiveSpec(BaseModel):
    minimum: Score = 0.95


class AssuranceToleranceSpec(BaseModel):
    corridor_loss: int = Field(default=1, ge=0, le=50)
    port_loss: int = Field(default=1, ge=0, le=50)
    communication_provider_loss: int = Field(default=1, ge=0, le=20)
    navigation_source_loss: int = Field(default=2, ge=0, le=20)
    observation_source_loss: int = Field(default=1, ge=0, le=20)


class AssuranceEvidenceSpec(BaseModel):
    minimum_independent_operational_sources: int = Field(default=2, ge=1, le=20)
    minimum_independent_navigation_sources: int = Field(default=3, ge=1, le=20)
    minimum_independent_environmental_sources: int = Field(default=2, ge=1, le=20)


class AssuranceCommercialSpec(BaseModel):
    minimum_carrier_options: int = Field(default=2, ge=1, le=20)
    insurance_required: bool = True


class AssuranceInventorySpec(BaseModel):
    minimum_reserve_days: int = Field(default=30, ge=0, le=3650)
    minimum_assured_replenishment_cycles: int = Field(default=1, ge=0, le=50)


class AssuranceRecoverySpec(BaseModel):
    verify_carrier_return: bool = True
    verify_backlog_clearance: bool = True
    verify_reserve_restoration: bool = True


class AssurancePolicySpec(BaseModel):
    continuity_objective: AssuranceObjectiveSpec = Field(default_factory=AssuranceObjectiveSpec)
    tolerate: AssuranceToleranceSpec = Field(default_factory=AssuranceToleranceSpec)
    evidence: AssuranceEvidenceSpec = Field(default_factory=AssuranceEvidenceSpec)
    commercial: AssuranceCommercialSpec = Field(default_factory=AssuranceCommercialSpec)
    inventory: AssuranceInventorySpec = Field(default_factory=AssuranceInventorySpec)
    recovery: AssuranceRecoverySpec = Field(default_factory=AssuranceRecoverySpec)

    @classmethod
    def from_camel_or_snake(cls, data: dict[str, Any]) -> AssurancePolicySpec:
        """Helper to normalize camelCase YAML keys from declarative specs."""
        mapping: dict[str, Any] = {}
        if "continuityObjective" in data or "continuity_objective" in data:
            raw_obj = data.get("continuityObjective") or data.get("continuity_objective") or {}
            mapping["continuity_objective"] = AssuranceObjectiveSpec(**raw_obj)
        if "tolerate" in data:
            raw_tol = data["tolerate"]
            mapping["tolerate"] = AssuranceToleranceSpec(
                corridor_loss=raw_tol.get("corridorLoss", raw_tol.get("corridor_loss", 1)),
                port_loss=raw_tol.get("portLoss", raw_tol.get("port_loss", 1)),
                communication_provider_loss=raw_tol.get(
                    "communicationProviderLoss", raw_tol.get("communication_provider_loss", 1)
                ),
                navigation_source_loss=raw_tol.get(
                    "navigationSourceLoss", raw_tol.get("navigation_source_loss", 2)
                ),
                observation_source_loss=raw_tol.get(
                    "observationSourceLoss", raw_tol.get("observation_source_loss", 1)
                ),
            )
        if "evidence" in data:
            raw_ev = data["evidence"]
            mapping["evidence"] = AssuranceEvidenceSpec(
                minimum_independent_operational_sources=raw_ev.get(
                    "minimumIndependentOperationalSources",
                    raw_ev.get("minimum_independent_operational_sources", 2),
                ),
                minimum_independent_navigation_sources=raw_ev.get(
                    "minimumIndependentNavigationSources",
                    raw_ev.get("minimum_independent_navigation_sources", 3),
                ),
                minimum_independent_environmental_sources=raw_ev.get(
                    "minimumIndependentEnvironmentalSources",
                    raw_ev.get("minimum_independent_environmental_sources", 2),
                ),
            )
        if "commercial" in data:
            raw_com = data["commercial"]
            mapping["commercial"] = AssuranceCommercialSpec(
                minimum_carrier_options=raw_com.get(
                    "minimumCarrierOptions", raw_com.get("minimum_carrier_options", 2)
                ),
                insurance_required=raw_com.get(
                    "insuranceRequired", raw_com.get("insurance_required", True)
                ),
            )
        if "inventory" in data:
            raw_inv = data["inventory"]
            mapping["inventory"] = AssuranceInventorySpec(
                minimum_reserve_days=raw_inv.get(
                    "minimumReserveDays", raw_inv.get("minimum_reserve_days", 30)
                ),
                minimum_assured_replenishment_cycles=raw_inv.get(
                    "minimumAssuredReplenishmentCycles",
                    raw_inv.get("minimum_assured_replenishment_cycles", 1),
                ),
            )
        if "recovery" in data:
            raw_rec = data["recovery"]
            mapping["recovery"] = AssuranceRecoverySpec(
                verify_carrier_return=raw_rec.get(
                    "verifyCarrierReturn", raw_rec.get("verify_carrier_return", True)
                ),
                verify_backlog_clearance=raw_rec.get(
                    "verifyBacklogClearance", raw_rec.get("verify_backlog_clearance", True)
                ),
                verify_reserve_restoration=raw_rec.get(
                    "verifyReserveRestoration", raw_rec.get("verify_reserve_restoration", True)
                ),
            )
        return cls(**mapping)


# --- RouteSubstitution spec ---


class RouteSubstitutionSpec(BaseModel):
    primary_route_id: str = Field(min_length=1, max_length=128)
    alternative_route_id: str = Field(min_length=1, max_length=128)
    cargo_type: str = Field(default="general")
    quantity: float = Field(gt=0)
    required_arrival_days: int = Field(ge=1, le=365)
    vessel_class_required: str | None = None
    ice_class_required: bool = False
    max_acceptable_delay_days: int = Field(default=14, ge=0, le=365)

    @classmethod
    def from_camel_or_snake(cls, data: dict[str, Any]) -> RouteSubstitutionSpec:
        return cls(
            primary_route_id=data.get("primaryRouteId", data.get("primary_route_id", "")),
            alternative_route_id=data.get(
                "alternativeRouteId", data.get("alternative_route_id", "")
            ),
            cargo_type=data.get("cargoType", data.get("cargo_type", "general")),
            quantity=float(data.get("quantity", 1000.0)),
            required_arrival_days=int(
                data.get("requiredArrivalDays", data.get("required_arrival_days", 30))
            ),
            vessel_class_required=data.get(
                "vesselClassRequired", data.get("vessel_class_required")
            ),
            ice_class_required=bool(
                data.get("iceClassRequired", data.get("ice_class_required", False))
            ),
            max_acceptable_delay_days=int(
                data.get("maxAcceptableDelayDays", data.get("max_acceptable_delay_days", 14))
            ),
        )


# --- Resource envelope ---


class Resource(BaseModel):
    """Top-level resource envelope for Continuity-as-Code YAML specifications."""

    api_version: str = Field(alias="apiVersion", default="continuity.io/v1")
    kind: ResourceKind
    metadata: ResourceMetadata
    spec: dict[str, Any]

    @model_validator(mode="after")
    def validate_spec_for_kind(self) -> Resource:
        """Validate that the spec is compatible with the declared kind."""
        # Validation is done at parse time through typed spec accessors
        return self

    def supply_network_spec(self) -> SupplyNetworkSpec:
        if self.kind != ResourceKind.SUPPLY_NETWORK:
            raise ValueError(f"expected SupplyNetwork, got {self.kind}")
        return SupplyNetworkSpec.model_validate(self.spec)

    def dependency_trust_spec(self) -> DependencyTrustSpec:
        if self.kind != ResourceKind.DEPENDENCY_TRUST:
            raise ValueError(f"expected DependencyTrust, got {self.kind}")
        return DependencyTrustSpec.model_validate(self.spec)

    def continuity_policy_spec(self) -> ContinuityPolicySpec:
        if self.kind != ResourceKind.CONTINUITY_POLICY:
            raise ValueError(f"expected ContinuityPolicy, got {self.kind}")
        return ContinuityPolicySpec.model_validate(self.spec)

    def scenario_spec(self) -> ScenarioSpec:
        if self.kind != ResourceKind.SCENARIO:
            raise ValueError(f"expected Scenario, got {self.kind}")
        return ScenarioSpec.model_validate(self.spec)

    def assurance_policy_spec(self) -> AssurancePolicySpec:
        if self.kind != ResourceKind.ASSURANCE_POLICY:
            raise ValueError(f"expected AssurancePolicy, got {self.kind}")
        return AssurancePolicySpec.from_camel_or_snake(self.spec)

    def route_substitution_spec(self) -> RouteSubstitutionSpec:
        if self.kind != ResourceKind.ROUTE_SUBSTITUTION:
            raise ValueError(f"expected RouteSubstitution, got {self.kind}")
        return RouteSubstitutionSpec.from_camel_or_snake(self.spec)


class ValidationError(BaseModel):
    """Actionable validation error for declarative specs."""

    path: str
    message: str
    severity: str = "error"


def load_resource(path: Path) -> Resource:
    """Load and validate a Continuity-as-Code YAML resource."""
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"expected a YAML object at document root: {path}")
    return Resource.model_validate(raw)


def load_resources(path: Path) -> list[Resource]:
    """Load all YAML resources from a file (supports multi-document YAML)."""
    with path.open("r", encoding="utf-8") as handle:
        documents = list(yaml.safe_load_all(handle))
    resources: list[Resource] = []
    for doc in documents:
        if doc is None:
            continue
        if not isinstance(doc, dict):
            raise ValueError(f"expected a YAML object in multi-document: {path}")
        resources.append(Resource.model_validate(doc))
    return resources


def validate_resource(resource: Resource) -> list[ValidationError]:
    """Validate a resource and return actionable errors."""
    errors: list[ValidationError] = []
    if resource.api_version != "continuity.io/v1":
        errors.append(
            ValidationError(
                path="apiVersion",
                message=f"unsupported API version: {resource.api_version}",
            )
        )
    try:
        if resource.kind == ResourceKind.SUPPLY_NETWORK:
            resource.supply_network_spec()
        elif resource.kind == ResourceKind.DEPENDENCY_TRUST:
            resource.dependency_trust_spec()
        elif resource.kind == ResourceKind.CONTINUITY_POLICY:
            resource.continuity_policy_spec()
        elif resource.kind == ResourceKind.SCENARIO:
            resource.scenario_spec()
        elif resource.kind == ResourceKind.ASSURANCE_POLICY:
            resource.assurance_policy_spec()
        elif resource.kind == ResourceKind.ROUTE_SUBSTITUTION:
            resource.route_substitution_spec()
    except Exception as exc:
        errors.append(
            ValidationError(
                path="spec",
                message=str(exc),
            )
        )
    return errors
