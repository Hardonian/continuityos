"""JSON Schema export and schema validation utilities for ContinuityOS DSL resources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from continuityos.dsl import (
    ContinuityPolicySpec,
    DependencyTrustSpec,
    Resource,
    ScenarioSpec,
    SupplyNetworkSpec,
)


def get_resource_schema() -> dict[str, Any]:
    """Return JSON Schema for the top-level Resource envelope."""
    return Resource.model_json_schema()


def get_supply_network_schema() -> dict[str, Any]:
    """Return JSON Schema for SupplyNetworkSpec."""
    return SupplyNetworkSpec.model_json_schema()


def get_continuity_policy_schema() -> dict[str, Any]:
    """Return JSON Schema for ContinuityPolicySpec."""
    return ContinuityPolicySpec.model_json_schema()


def get_dependency_trust_schema() -> dict[str, Any]:
    """Return JSON Schema for DependencyTrustSpec."""
    return DependencyTrustSpec.model_json_schema()


def get_scenario_schema() -> dict[str, Any]:
    """Return JSON Schema for ScenarioSpec."""
    return ScenarioSpec.model_json_schema()


def export_all_schemas(output_dir: Path) -> dict[str, Path]:
    """Export all JSON Schema files to a target directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    schemas = {
        "resource.schema.json": get_resource_schema(),
        "supply-network.schema.json": get_supply_network_schema(),
        "continuity-policy.schema.json": get_continuity_policy_schema(),
        "dependency-trust.schema.json": get_dependency_trust_schema(),
        "scenario.schema.json": get_scenario_schema(),
    }
    paths: dict[str, Path] = {}
    for filename, schema_dict in schemas.items():
        out_path = output_dir / filename
        out_path.write_text(json.dumps(schema_dict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[filename] = out_path
    return paths
