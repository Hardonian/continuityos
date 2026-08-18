"""Tests for the Continuity-as-Code DSL module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from continuityos.dsl import (
    Resource,
    ResourceKind,
    load_resource,
    load_resources,
    validate_resource,
)

VALID_SUPPLY_NETWORK_YAML = """\
apiVersion: continuity.io/v1
kind: SupplyNetwork
metadata:
  name: arctic-supply-network
  namespace: default
  labels:
    region: arctic
spec:
  objectives:
    minimum_continuity: 0.95
    maximum_critical_shortage_days: 7
    maximum_recovery_days: 30
  redundancy:
    minimum_routes: 3
    minimum_ports: 2
    minimum_satcom_providers: 2
  inventory:
    fuel_reserve_days: 30
    medical_reserve_days: 60
"""


VALID_POLICY_YAML = """\
apiVersion: continuity.io/v1
kind: ContinuityPolicy
metadata:
  name: arctic-resilience
spec:
  rules:
    - rule_id: SAT-001
      description: SATCOM must have redundant providers
      assertion:
        minimum_providers: 2
    - rule_id: INV-001
      description: Fuel reserves must exceed 30 days
      assertion:
        minimum_reserve_days: 30
"""


VALID_TRUST_YAML = """\
apiVersion: continuity.io/v1
kind: DependencyTrust
metadata:
  name: satcom-trust
spec:
  dependency_ref: satcom/iridium
  dimensions:
    physical_availability: 0.95
    cyber_integrity: 0.8
    legal_availability: 1.0
    commercial_availability: 0.9
  strategy:
    aggregation: minimum
  provenance:
    minimum_independent_sources: 2
"""


VALID_SCENARIO_YAML = """\
apiVersion: continuity.io/v1
kind: Scenario
metadata:
  name: nsr-closure
spec:
  events:
    - target: corridor/nsr
      state: physically_closed
      description: NSR closed due to heavy ice
    - target: port/murmansk
      state: functionally_closed
      description: Port congested
  duration_days: 60
"""


class TestResourceParsing:
    def test_parse_supply_network(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_SUPPLY_NETWORK_YAML)
            f.flush()
            resource = load_resource(Path(f.name))
        assert resource.kind == ResourceKind.SUPPLY_NETWORK
        assert resource.metadata.name == "arctic-supply-network"
        spec = resource.supply_network_spec()
        assert spec.objectives.minimum_continuity == 0.95
        assert spec.redundancy.minimum_routes == 3
        assert spec.inventory.fuel_reserve_days == 30

    def test_parse_policy(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_POLICY_YAML)
            f.flush()
            resource = load_resource(Path(f.name))
        assert resource.kind == ResourceKind.CONTINUITY_POLICY
        spec = resource.continuity_policy_spec()
        assert len(spec.rules) == 2
        assert spec.rules[0].rule_id == "SAT-001"

    def test_parse_trust(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_TRUST_YAML)
            f.flush()
            resource = load_resource(Path(f.name))
        assert resource.kind == ResourceKind.DEPENDENCY_TRUST
        spec = resource.dependency_trust_spec()
        assert spec.dependency_ref == "satcom/iridium"
        assert spec.dimensions.physical_availability == 0.95

    def test_parse_scenario(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_SCENARIO_YAML)
            f.flush()
            resource = load_resource(Path(f.name))
        assert resource.kind == ResourceKind.SCENARIO
        spec = resource.scenario_spec()
        assert len(spec.events) == 2
        assert spec.duration_days == 60

    def test_load_multi_document(self) -> None:
        combined = VALID_SUPPLY_NETWORK_YAML + "\n---\n" + VALID_POLICY_YAML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(combined)
            f.flush()
            resources = load_resources(Path(f.name))
        assert len(resources) == 2
        assert resources[0].kind == ResourceKind.SUPPLY_NETWORK
        assert resources[1].kind == ResourceKind.CONTINUITY_POLICY


class TestResourceValidation:
    def test_valid_resource_no_errors(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(VALID_SUPPLY_NETWORK_YAML)
            f.flush()
            resource = load_resource(Path(f.name))
        errors = validate_resource(resource)
        assert errors == []

    def test_invalid_api_version(self) -> None:
        resource = Resource.model_validate(
            {
                "apiVersion": "wrong/v99",
                "kind": "SupplyNetwork",
                "metadata": {"name": "test"},
                "spec": {},
            }
        )
        errors = validate_resource(resource)
        assert any("unsupported API version" in e.message for e in errors)

    def test_wrong_kind_accessor(self) -> None:
        resource = Resource.model_validate(
            {
                "apiVersion": "continuity.io/v1",
                "kind": "Scenario",
                "metadata": {"name": "test"},
                "spec": {"events": [{"target": "x", "state": "open"}]},
            }
        )
        with pytest.raises(ValueError, match="expected SupplyNetwork"):
            resource.supply_network_spec()
