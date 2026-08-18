"""Tests for JSON Schema generation and export utilities."""

from __future__ import annotations

from pathlib import Path

from continuityos.schemas import (
    export_all_schemas,
    get_continuity_policy_schema,
    get_dependency_trust_schema,
    get_resource_schema,
    get_scenario_schema,
    get_supply_network_schema,
)


class TestSchemas:
    def test_schema_generators(self) -> None:
        assert "$defs" in get_resource_schema() or "properties" in get_resource_schema()
        assert "properties" in get_supply_network_schema()
        assert "properties" in get_continuity_policy_schema()
        assert "properties" in get_dependency_trust_schema()
        assert "properties" in get_scenario_schema()

    def test_export_all_schemas(self, tmp_path: Path) -> None:
        paths = export_all_schemas(tmp_path / "schemas_test")
        assert len(paths) == 5
        assert (tmp_path / "schemas_test" / "resource.schema.json").exists()
        assert (tmp_path / "schemas_test" / "supply-network.schema.json").exists()
        assert (tmp_path / "schemas_test" / "continuity-policy.schema.json").exists()
        assert (tmp_path / "schemas_test" / "dependency-trust.schema.json").exists()
        assert (tmp_path / "schemas_test" / "scenario.schema.json").exists()
