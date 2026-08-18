"""Tests for enhanced dependency graph engine: cycle detection, alternative paths, blast radius."""

from __future__ import annotations

from continuityos.graph import (
    DependencyEdge,
    DependencyEngine,
    DependencyGraph,
    DependencyNode,
    detect_cycles,
)


def _sample_graph() -> DependencyGraph:
    nodes = [
        DependencyNode(node_id="port_a", name="Port A", node_type="port", criticality=0.9),
        DependencyNode(node_id="route_1", name="Route 1", node_type="corridor", criticality=0.8),
        DependencyNode(node_id="route_2", name="Route 2", node_type="corridor", criticality=0.8),
        DependencyNode(node_id="port_b", name="Port B", node_type="port", criticality=0.9),
        DependencyNode(node_id="satcom", name="SATCOM", node_type="satcom", criticality=0.7),
    ]
    edges = [
        DependencyEdge(source="satcom", target="route_1", dependency_strength=0.8),
        DependencyEdge(source="satcom", target="route_2", dependency_strength=0.8),
        DependencyEdge(source="port_a", target="route_1", dependency_strength=0.9),
        DependencyEdge(source="port_a", target="route_2", dependency_strength=0.9),
        DependencyEdge(source="route_1", target="port_b", dependency_strength=0.9),
        DependencyEdge(source="route_2", target="port_b", dependency_strength=0.9),
    ]
    return DependencyGraph(graph_id="arctic-network", nodes=nodes, edges=edges)


class TestEnhancedGraph:
    def test_detect_cycles_acyclic(self) -> None:
        graph = _sample_graph()
        cycles = detect_cycles(graph)
        assert len(cycles) == 0

    def test_detect_cycles_cyclic(self) -> None:
        nodes = [
            DependencyNode(node_id="A", name="Node A", node_type="facility", criticality=0.5),
            DependencyNode(node_id="B", name="Node B", node_type="facility", criticality=0.5),
            DependencyNode(node_id="C", name="Node C", node_type="facility", criticality=0.5),
        ]
        edges = [
            DependencyEdge(source="A", target="B", dependency_strength=1.0),
            DependencyEdge(source="B", target="C", dependency_strength=1.0),
            DependencyEdge(source="C", target="A", dependency_strength=1.0),
        ]
        graph = DependencyGraph(graph_id="cyclic-graph", nodes=nodes, edges=edges)
        cycles = detect_cycles(graph)
        assert len(cycles) > 0
        assert any(c[0] == c[-1] for c in cycles)

    def test_find_alternative_paths(self) -> None:
        engine = DependencyEngine()
        graph = _sample_graph()
        paths = engine.find_alternative_paths(graph, "port_a", "port_b", failed=set())
        assert len(paths) == 2
        assert ["port_a", "route_1", "port_b"] in paths
        assert ["port_a", "route_2", "port_b"] in paths

        # Fail route_1
        paths_with_failure = engine.find_alternative_paths(graph, "port_a", "port_b", failed={"route_1"})
        assert len(paths_with_failure) == 1
        assert paths_with_failure[0] == ["port_a", "route_2", "port_b"]

    def test_calculate_blast_radius(self) -> None:
        engine = DependencyEngine()
        graph = _sample_graph()
        radius = engine.calculate_blast_radius(graph, {"satcom"})
        assert "satcom" in radius
        assert radius["satcom"] == 1.0
        assert radius.get("route_1", 0) > 0
        assert radius.get("route_2", 0) > 0
        assert radius.get("port_b", 0) > 0
