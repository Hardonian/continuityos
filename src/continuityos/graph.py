from __future__ import annotations

from collections import defaultdict, deque
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from continuityos.domain import GeoPoint, Score


class NodeType(StrEnum):
    CORRIDOR = "corridor"
    PORT = "port"
    AIRFIELD = "airfield"
    VESSEL = "vessel"
    ICEBREAKER = "icebreaker"
    FUEL = "fuel"
    POWER = "power"
    INVENTORY = "inventory"
    SATCOM = "satcom"
    TERRESTRIAL_NETWORK = "terrestrial_network"
    IDENTITY_PROVIDER = "identity_provider"
    CLOUD_SERVICE = "cloud_service"
    PORT_OT = "port_ot"
    DATA_FEED = "data_feed"
    SUPPLIER = "supplier"
    CARRIER = "carrier"
    COMMUNITY = "community"
    FACILITY = "facility"


class DependencyKind(StrEnum):
    REQUIRES = "requires"
    TRANSPORTS = "transports"
    AUTHENTICATES = "authenticates"
    POWERS = "powers"
    CONNECTS = "connects"
    SUPPLIES = "supplies"
    VALIDATES = "validates"


class DependencyNode(BaseModel):
    node_id: str
    name: str
    node_type: NodeType
    criticality: Score = 0.5
    location: GeoPoint | None = None
    provider_id: str | None = None
    attributes: dict[str, str | float | int | bool] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    source: str
    target: str
    kind: DependencyKind = DependencyKind.REQUIRES
    dependency_strength: Score = 1.0
    substitutable: bool = False
    substitute_group: str | None = None


class DependencyGraph(BaseModel):
    graph_id: str
    nodes: list[DependencyNode]
    edges: list[DependencyEdge]

    @model_validator(mode="after")
    def validate_references(self) -> DependencyGraph:
        ids = {node.node_id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("node ids must be unique")
        for edge in self.edges:
            if edge.source not in ids or edge.target not in ids:
                raise ValueError(f"edge references unknown node: {edge.source}->{edge.target}")
        return self


class ImpactedNode(BaseModel):
    node_id: str
    impact_probability: Score
    weighted_impact: float = Field(ge=0)
    path: list[str]


class GraphAssessment(BaseModel):
    graph_id: str
    failed_nodes: list[str]
    impacted_nodes: list[ImpactedNode]
    total_weighted_impact: float = Field(ge=0)
    provider_concentration: dict[str, int]
    single_points_of_failure: list[str]


class DependencyEngine:
    """Deterministic downstream impact propagation over a directed dependency graph.

    Edge source is the dependency; edge target is the dependent system. An outage at
    source therefore propagates toward target. Substitutable edges are attenuated when
    another healthy member of the same substitute group exists.
    """

    def analyze(self, graph: DependencyGraph, failed_nodes: set[str]) -> GraphAssessment:
        nodes = {node.node_id: node for node in graph.nodes}
        unknown = failed_nodes - nodes.keys()
        if unknown:
            raise ValueError(f"unknown failed nodes: {sorted(unknown)}")

        outgoing: dict[str, list[DependencyEdge]] = defaultdict(list)
        substitute_members: dict[str, set[str]] = defaultdict(set)
        provider_counts: dict[str, int] = defaultdict(int)
        for node in graph.nodes:
            if node.provider_id:
                provider_counts[node.provider_id] += 1
        for edge in graph.edges:
            outgoing[edge.source].append(edge)
            if edge.substitute_group:
                substitute_members[edge.substitute_group].add(edge.source)

        probability: dict[str, float] = {node_id: 1.0 for node_id in failed_nodes}
        best_path: dict[str, list[str]] = {node_id: [node_id] for node_id in failed_nodes}
        queue: deque[str] = deque(sorted(failed_nodes))
        while queue:
            current = queue.popleft()
            current_probability = probability[current]
            for edge in sorted(outgoing.get(current, []), key=lambda item: item.target):
                attenuation = 1.0
                if edge.substitutable and edge.substitute_group:
                    healthy_alternatives = (
                        substitute_members[edge.substitute_group] - failed_nodes - {current}
                    )
                    if healthy_alternatives:
                        attenuation = 0.25
                propagated = current_probability * edge.dependency_strength * attenuation
                existing = probability.get(edge.target, 0.0)
                combined = 1.0 - (1.0 - existing) * (1.0 - propagated)
                if combined > existing + 1e-9:
                    probability[edge.target] = min(1.0, combined)
                    best_path[edge.target] = best_path[current] + [edge.target]
                    queue.append(edge.target)

        impacted = [
            ImpactedNode(
                node_id=node_id,
                impact_probability=round(probability_value, 6),
                weighted_impact=round(probability_value * nodes[node_id].criticality, 6),
                path=best_path[node_id],
            )
            for node_id, probability_value in probability.items()
        ]
        impacted.sort(key=lambda item: (-item.weighted_impact, item.node_id))

        single_points = self._single_points(graph, nodes)
        return GraphAssessment(
            graph_id=graph.graph_id,
            failed_nodes=sorted(failed_nodes),
            impacted_nodes=impacted,
            total_weighted_impact=round(sum(item.weighted_impact for item in impacted), 6),
            provider_concentration=dict(sorted(provider_counts.items())),
            single_points_of_failure=single_points,
        )

    def _single_points(self, graph: DependencyGraph, nodes: dict[str, DependencyNode]) -> list[str]:
        result: list[str] = []
        for candidate in sorted(nodes):
            assessment = self.analyze_without_spof(graph, {candidate})
            affected_critical = [
                item
                for item in assessment
                if nodes[item.node_id].criticality >= 0.8 and item.impact_probability >= 0.7
            ]
            if affected_critical and any(item.node_id != candidate for item in affected_critical):
                result.append(candidate)
        return result

    def analyze_without_spof(
        self, graph: DependencyGraph, failed_nodes: set[str]
    ) -> list[ImpactedNode]:
        """Internal propagation used to avoid recursive SPOF analysis."""
        nodes = {node.node_id: node for node in graph.nodes}
        outgoing: dict[str, list[DependencyEdge]] = defaultdict(list)
        substitute_members: dict[str, set[str]] = defaultdict(set)
        for edge in graph.edges:
            outgoing[edge.source].append(edge)
            if edge.substitute_group:
                substitute_members[edge.substitute_group].add(edge.source)
        probability = {node_id: 1.0 for node_id in failed_nodes}
        paths = {node_id: [node_id] for node_id in failed_nodes}
        queue: deque[str] = deque(sorted(failed_nodes))
        while queue:
            current = queue.popleft()
            for edge in outgoing.get(current, []):
                attenuation = 1.0
                if edge.substitutable and edge.substitute_group:
                    healthy = substitute_members[edge.substitute_group] - failed_nodes - {current}
                    if healthy:
                        attenuation = 0.25
                propagated = probability[current] * edge.dependency_strength * attenuation
                existing = probability.get(edge.target, 0.0)
                combined = 1.0 - (1.0 - existing) * (1.0 - propagated)
                if combined > existing + 1e-9:
                    probability[edge.target] = min(1.0, combined)
                    paths[edge.target] = paths[current] + [edge.target]
                    queue.append(edge.target)
        return [
            ImpactedNode(
                node_id=node_id,
                impact_probability=value,
                weighted_impact=value * nodes[node_id].criticality,
                path=paths[node_id],
            )
            for node_id, value in probability.items()
        ]
