"""Provider Independence Analyzer.

Detects false redundancy across communications, navigation, suppliers,
ports, routes, carriers, data sources, fuel, and warehouses by analyzing
upstream shared dependencies (e.g., common gateways, backhaul transit,
power grids, upstream satellite constellations, and legal jurisdictions).
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.graph import DependencyGraph


class SharedDependency(BaseModel):
    """An upstream dependency shared across multiple nominally independent providers."""

    dependency_id: str
    dependency_name: str
    dependency_type: str
    shared_by_providers: list[str]


class IndependenceResult(BaseModel):
    """Analysis result for a specific category of providers."""

    category: str
    declared_providers: list[str]
    declared_count: int
    independent_count: int
    shared_dependencies: list[SharedDependency]
    redundancy_valid: bool
    justification: str

    def format_text(self) -> str:
        """Format as human-readable report."""
        lines = [
            f"Category:             {self.category.upper()}",
            f"Declared providers:   {self.declared_count} ({', '.join(self.declared_providers)})",
            f"Independent providers:{self.independent_count}",
            "",
        ]
        if self.shared_dependencies:
            lines.append("Shared dependencies:")
            for sd in self.shared_dependencies:
                lines.append(
                    f"  * {sd.dependency_id} ({sd.dependency_type}) -> shared by: {', '.join(sd.shared_by_providers)}"
                )
            lines.append("")
        else:
            lines.append("No shared upstream dependencies detected.")
            lines.append("")
        status = "REDUNDANCY VALID" if self.redundancy_valid else "REDUNDANCY INVALID"
        lines.append(f"Result:\n{status}")
        return "\n".join(lines)


class ProviderIndependenceReport(BaseModel):
    """Holistic multi-category provider independence assessment."""

    report_id: UUID = Field(default_factory=uuid4)
    overall_valid: bool
    results: dict[str, IndependenceResult]
    summary: str

    def format_text(self) -> str:
        lines = [
            "=" * 78,
            "PROVIDER INDEPENDENCE & FALSE REDUNDANCY AUDIT",
            "=" * 78,
            f"Overall Status: {'VALID (NO FALSE REDUNDANCY)' if self.overall_valid else 'INVALID (FALSE REDUNDANCY DETECTED)'}",
            f"Summary:        {self.summary}",
            "=" * 78,
            "",
        ]
        for res in self.results.values():
            lines.append(res.format_text())
            lines.append("-" * 78)
        return "\n".join(lines)


class ProviderIndependenceAnalyzer:
    """Analyzes dependency graphs to detect shared upstream dependencies among declared providers."""

    def __init__(self, graph: DependencyGraph | None = None) -> None:
        self.graph = graph

    def get_upstream_dependencies(
        self, graph: DependencyGraph, node_id: str, visited: set[str] | None = None
    ) -> set[str]:
        """Find all upstream dependencies for a node (nodes that this node requires/connects to).

        In ContinuityOS graphs:
        - edge.source is dependency, edge.target is dependent system (target requires source).
        - So for a node as target, upstream dependencies are edge.source!
        """
        if visited is None:
            visited = set()
        if node_id in visited:
            return set()
        visited.add(node_id)

        upstream: set[str] = set()
        for edge in graph.edges:
            if edge.target == node_id and edge.source != node_id:
                upstream.add(edge.source)
                upstream.update(self.get_upstream_dependencies(graph, edge.source, visited))
        return upstream

    def analyze_category(
        self,
        graph: DependencyGraph,
        category: str,
        provider_node_ids: list[str],
        minimum_required: int = 2,
    ) -> IndependenceResult:
        """Analyze a list of provider nodes for upstream shared dependencies."""
        nodes_by_id = {node.node_id: node for node in graph.nodes}
        declared_count = len(provider_node_ids)

        if declared_count == 0:
            return IndependenceResult(
                category=category,
                declared_providers=[],
                declared_count=0,
                independent_count=0,
                shared_dependencies=[],
                redundancy_valid=False,
                justification="No providers declared for category",
            )

        # Collect upstream dependencies and attributes for each provider
        provider_upstreams: dict[str, set[str]] = {}
        for pid in provider_node_ids:
            up = self.get_upstream_dependencies(graph, pid)
            provider_upstreams[pid] = up

        # Also inspect direct attributes that might indicate shared backhaul/gateway/power/jurisdiction
        attr_keys = [
            "gateway",
            "ground_station",
            "backhaul_provider",
            "transit_provider",
            "power_source",
            "power_grid",
            "jurisdiction",
            "satellite_provider",
            "upstream_supplier",
            "port_terminal",
        ]

        shared_deps_map: dict[str, SharedDependency] = {}

        # 1. Check graph upstream node intersection
        upstream_counts: dict[str, list[str]] = defaultdict(list)
        for pid, up_nodes in provider_upstreams.items():
            for u in up_nodes:
                upstream_counts[u].append(pid)

        for u_id, pids in upstream_counts.items():
            if len(set(pids)) > 1:
                u_node = nodes_by_id.get(u_id)
                u_name = u_node.name if u_node else u_id
                u_type = u_node.node_type.value if u_node else "upstream_node"
                shared_deps_map[u_id] = SharedDependency(
                    dependency_id=u_id,
                    dependency_name=u_name,
                    dependency_type=u_type,
                    shared_by_providers=sorted(set(pids)),
                )

        # 2. Check attribute-level shared dependencies
        for key in attr_keys:
            val_to_pids: dict[str, list[str]] = defaultdict(list)
            for pid in provider_node_ids:
                node = nodes_by_id.get(pid)
                if node and key in node.attributes:
                    val = str(node.attributes[key])
                    val_to_pids[val].append(pid)
            for val, pids in val_to_pids.items():
                if len(set(pids)) > 1:
                    dep_key = f"{key}/{val}"
                    if dep_key not in shared_deps_map:
                        shared_deps_map[dep_key] = SharedDependency(
                            dependency_id=dep_key,
                            dependency_name=f"Shared {key}: {val}",
                            dependency_type=key,
                            shared_by_providers=sorted(set(pids)),
                        )

        # Calculate effective independent providers
        # If two providers share a critical upstream dependency, collapse their independence
        shared_list = sorted(shared_deps_map.values(), key=lambda x: x.dependency_id)

        # Disjoint set / clustering to find true independent groups
        parent: dict[str, str] = {pid: pid for pid in provider_node_ids}

        def find(i: str) -> str:
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i: str, j: str) -> None:
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        for sd in shared_list:
            pids = sd.shared_by_providers
            for i in range(len(pids) - 1):
                union(pids[i], pids[i + 1])

        unique_roots = {find(pid) for pid in provider_node_ids}
        independent_count = len(unique_roots)
        redundancy_valid = (
            independent_count >= minimum_required
            if declared_count >= minimum_required
            else independent_count == declared_count
        )

        if not redundancy_valid and declared_count >= minimum_required:
            justification = (
                f"Declared {declared_count} providers, but shared upstream dependencies "
                f"({', '.join(sd.dependency_id for sd in shared_list)}) reduce effective independent providers to {independent_count}."
            )
        else:
            justification = f"All {independent_count} declared provider(s) have verified independent upstream dependencies."

        return IndependenceResult(
            category=category,
            declared_providers=sorted(provider_node_ids),
            declared_count=declared_count,
            independent_count=independent_count,
            shared_dependencies=shared_list,
            redundancy_valid=redundancy_valid,
            justification=justification,
        )

    def analyze_graph(
        self,
        graph: DependencyGraph,
        provider_categories: dict[str, list[str]] | None = None,
    ) -> ProviderIndependenceReport:
        """Run independence analysis across all specified or auto-discovered categories in the graph."""
        if provider_categories is None:
            # Auto-group nodes by category
            groups: dict[str, list[str]] = defaultdict(list)
            for node in graph.nodes:
                nt = node.node_type.value
                if nt in {"satcom", "terrestrial_network"}:
                    groups["communications"].append(node.node_id)
                elif nt in {"data_feed"}:
                    groups["data_sources"].append(node.node_id)
                elif nt in {"port", "port_ot"}:
                    groups["ports"].append(node.node_id)
                elif nt in {"carrier", "vessel"}:
                    groups["carriers"].append(node.node_id)
                elif nt in {"supplier", "mine_or_refinery"}:
                    groups["suppliers"].append(node.node_id)
                elif nt in {"corridor"}:
                    groups["routes"].append(node.node_id)
                elif nt in {"fuel", "inventory", "strategic_stockpile"}:
                    groups["fuel_and_inventory"].append(node.node_id)
            provider_categories = groups

        results: dict[str, IndependenceResult] = {}
        for category, pids in provider_categories.items():
            if len(pids) >= 2:
                results[category] = self.analyze_category(graph, category, pids)

        all_valid = all(res.redundancy_valid for res in results.values()) if results else True
        invalid_count = sum(1 for res in results.values() if not res.redundancy_valid)
        summary = (
            "All provider groups verified truly independent."
            if all_valid
            else f"False redundancy detected in {invalid_count} category/categories: {', '.join(k for k, v in results.items() if not v.redundancy_valid)}."
        )

        return ProviderIndependenceReport(
            overall_valid=all_valid,
            results=results,
            summary=summary,
        )
