"""Ecosystem Integrations for ContinuityOS.

Provides first-class interfaces for:
- Terraform / OpenTofu Provider schema generation and state mapping
- Kubernetes Custom Resource Definitions (CRDs) & Reconciliation Controller loop
- Open Policy Agent (OPA) / Rego policy evaluation for automated CI/CD gating
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from continuityos.domain import CorridorState


class TerraformProviderSchema:
    """Generates official Terraform / OpenTofu Provider specifications."""

    @staticmethod
    def get_provider_schema() -> dict[str, Any]:
        """Return the Terraform provider schema for terraform-provider-continuityos."""
        return {
            "provider": {
                "name": "continuityos",
                "version": "1.0.0",
                "description": "Terraform / OpenTofu Provider for Resilience-as-Code",
                "attributes": {
                    "endpoint": {
                        "type": "string",
                        "description": "ContinuityOS Sovereign Service API Endpoint",
                        "default": "http://127.0.0.1:8082",
                    },
                    "api_key": {
                        "type": "string",
                        "sensitive": True,
                        "description": "API Key or Sovereign SCIF Token",
                    },
                    "offline_mode": {
                        "type": "bool",
                        "description": "Enforce zero-cloud air-gapped local execution",
                        "default": True,
                    },
                },
                "resources": {
                    "continuity_corridor": {
                        "description": "Declares a critical mission corridor and resilience thresholds",
                        "attributes": {
                            "name": {"type": "string", "required": True},
                            "origin": {"type": "string", "required": True},
                            "destination": {"type": "string", "required": True},
                            "required_redundancy": {"type": "number", "default": 2},
                            "max_recovery_lag_t5_days": {"type": "number", "default": 14.0},
                            "closure_threshold": {"type": "number", "default": 0.70},
                        },
                    },
                    "continuity_policy": {
                        "description": "Declares automated resilience policy evaluation rules",
                        "attributes": {
                            "name": {"type": "string", "required": True},
                            "target_network": {"type": "string", "required": True},
                            "min_healthy_providers": {"type": "number", "default": 2},
                            "min_inventory_buffer_days": {"type": "number", "default": 30.0},
                        },
                    },
                    "continuity_assurance": {
                        "description": "Declares resilience budget gates and verification rules",
                        "attributes": {
                            "name": {"type": "string", "required": True},
                            "min_resilience_budget": {"type": "number", "default": 0.85},
                        },
                    },
                },
            }
        }


class KubernetesCRDGenerator:
    """Generates standard Kubernetes CustomResourceDefinitions (CRDs) for cloud-native deployment."""

    @staticmethod
    def generate_corridor_crd() -> dict[str, Any]:
        """Generate CustomResourceDefinition for kind: MissionCorridor."""
        return {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "metadata": {"name": "missioncorridors.continuity.io"},
            "spec": {
                "group": "continuity.io",
                "versions": [
                    {
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "spec": {
                                        "type": "object",
                                        "properties": {
                                            "origin": {"type": "string"},
                                            "destination": {"type": "string"},
                                            "requiredRedundancy": {"type": "integer"},
                                            "maxRecoveryLagDays": {"type": "number"},
                                        },
                                        "required": ["origin", "destination"],
                                    },
                                    "status": {
                                        "type": "object",
                                        "properties": {
                                            "effectiveState": {"type": "string"},
                                            "resilienceScore": {"type": "number"},
                                            "closureReason": {"type": "string"},
                                            "lastReconciled": {"type": "string"},
                                        },
                                    },
                                },
                            }
                        },
                        "subresources": {"status": {}},
                    }
                ],
                "scope": "Namespaced",
                "names": {
                    "plural": "missioncorridors",
                    "singular": "missioncorridor",
                    "kind": "MissionCorridor",
                    "shortNames": ["mc"],
                },
            },
        }

    @staticmethod
    def generate_supply_network_crd() -> dict[str, Any]:
        """Generate CustomResourceDefinition for kind: SupplyNetwork."""
        return {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "metadata": {"name": "supplynetworks.continuity.io"},
            "spec": {
                "group": "continuity.io",
                "versions": [
                    {
                        "name": "v1",
                        "served": True,
                        "storage": True,
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "spec": {
                                        "type": "object",
                                        "properties": {
                                            "primaryCorridors": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "declaredRedundancy": {"type": "integer"},
                                            "requiredProviders": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                        },
                                    },
                                    "status": {
                                        "type": "object",
                                        "properties": {
                                            "healthScore": {"type": "number"},
                                            "activeSPOFs": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "compliant": {"type": "boolean"},
                                        },
                                    },
                                },
                            }
                        },
                        "subresources": {"status": {}},
                    }
                ],
                "scope": "Namespaced",
                "names": {
                    "plural": "supplynetworks",
                    "singular": "supplynetwork",
                    "kind": "SupplyNetwork",
                    "shortNames": ["sn"],
                },
            },
        }


class KubernetesReconciliationResult(BaseModel):
    """Result emitted by the ContinuityOS Kubernetes reconciliation controller loop."""

    resource_name: str
    resource_kind: str
    effective_state: CorridorState
    resilience_score: float
    is_compliant: bool
    closure_reasons: list[str] = Field(default_factory=list)
    reconciled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KubernetesController:
    """Simulates/implements the in-cluster Kubernetes operator reconciliation loop."""

    @staticmethod
    def reconcile_corridor(
        spec: dict[str, Any],
        live_telemetry: dict[str, Any] | None = None,
    ) -> KubernetesReconciliationResult:
        """Reconcile a declared MissionCorridor against live telemetry."""
        name = str(spec.get("metadata", {}).get("name", "corridor-unnamed"))
        props = spec.get("spec", spec)

        _req_redundancy = int(props.get("requiredRedundancy", props.get("required_redundancy", 2)))
        max_lag = float(props.get("maxRecoveryLagDays", props.get("max_recovery_lag_days", 14.0)))

        # Evaluate against live telemetry
        effective_state = CorridorState.OPEN
        resilience_score = 1.0
        closure_reasons: list[str] = []

        if live_telemetry:
            is_physically_closed = bool(live_telemetry.get("physically_closed", False))
            is_uninsurable = bool(live_telemetry.get("uninsurable", False))
            is_gnss_denied = bool(live_telemetry.get("gnss_denied", False))
            active_lag_days = float(live_telemetry.get("recovery_lag_days", 0.0))

            if is_physically_closed:
                effective_state = CorridorState.PHYSICALLY_CLOSED
                resilience_score = 0.0
                closure_reasons.append("PHYSICAL_OBSTRUCTION")
            elif is_uninsurable:
                effective_state = CorridorState.OPEN_BUT_UNINSURABLE
                resilience_score = 0.35
                closure_reasons.append("WAR_RISK_UNDERWRITER_WITHDRAWAL")
            elif is_gnss_denied:
                effective_state = CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED
                resilience_score = 0.45
                closure_reasons.append("GNSS_EW_SPOOFING")

            if active_lag_days > max_lag:
                effective_state = CorridorState.RECOVERY_BACKLOGGED
                resilience_score = min(resilience_score, 0.40)
                closure_reasons.append(f"RECOVERY_LAG_{active_lag_days}D_EXCEEDS_{max_lag}D")

        is_compliant = resilience_score >= 0.70 and effective_state not in {
            CorridorState.PHYSICALLY_CLOSED,
            CorridorState.FUNCTIONALLY_CLOSED,
        }

        return KubernetesReconciliationResult(
            resource_name=name,
            resource_kind="MissionCorridor",
            effective_state=effective_state,
            resilience_score=resilience_score,
            is_compliant=is_compliant,
            closure_reasons=closure_reasons,
        )


class OPAGateEvaluation(BaseModel):
    """Result of an Open Policy Agent (OPA) / Rego CI/CD gating evaluation."""

    policy_name: str
    allowed: bool
    violations: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    rules_checked: int = 0


class OPAGatekeeper:
    """Evaluates supply chain commitments and procurement against automated OPA/Rego policies."""

    @staticmethod
    def evaluate_gate(
        policy_rules: dict[str, Any],
        proposed_action_or_state: dict[str, Any],
    ) -> OPAGateEvaluation:
        """Evaluate whether a proposed operational route or procurement plan passes resilience gates."""
        policy_name = str(policy_rules.get("name", "standard-resilience-gate"))
        min_redundancy = int(policy_rules.get("min_redundancy", 2))
        max_closure_risk = float(policy_rules.get("max_closure_risk", 0.40))
        min_assured_replenishment_days = float(
            policy_rules.get("min_assured_replenishment_days", 30.0)
        )
        prohibit_unhedged_spof = bool(policy_rules.get("prohibit_unhedged_spof", True))

        violations: list[str] = []
        rules_checked = 4

        # 1. Redundancy check
        available_routes = int(proposed_action_or_state.get("available_routes", 1))
        if available_routes < min_redundancy:
            violations.append(
                f"REDUNDANCY_VIOLATION: Required {min_redundancy} routes, but only {available_routes} available"
            )

        # 2. Risk threshold check
        closure_prob = float(proposed_action_or_state.get("closure_probability", 0.0))
        if closure_prob > max_closure_risk:
            violations.append(
                f"RISK_VIOLATION: Corridor closure risk {closure_prob:.2f} exceeds threshold {max_closure_risk:.2f}"
            )

        # 3. Replenishment horizon check
        replenishment_days = float(proposed_action_or_state.get("assured_replenishment_days", 45.0))
        if replenishment_days < min_assured_replenishment_days:
            violations.append(
                f"STOCKPILE_VIOLATION: Assured replenishment {replenishment_days:.1f}d below minimum {min_assured_replenishment_days:.1f}d"
            )

        # 4. SPOF check
        has_unhedged_spof = bool(proposed_action_or_state.get("has_unhedged_spof", False))
        if prohibit_unhedged_spof and has_unhedged_spof:
            violations.append(
                "SPOF_VIOLATION: Route commits to single-point-of-failure transit without verified substitute"
            )

        allowed = len(violations) == 0
        return OPAGateEvaluation(
            policy_name=policy_name,
            allowed=allowed,
            violations=violations,
            rules_checked=rules_checked,
        )
