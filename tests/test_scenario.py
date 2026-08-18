"""Tests for Correlated Failure Scenario engine."""

from __future__ import annotations

from continuityos.domain import CorridorState
from continuityos.graph import DependencyEdge, DependencyGraph, DependencyNode
from continuityos.scenario import (
    Scenario,
    ScenarioEvent,
    simulate_scenario,
)


def _sample_graph() -> DependencyGraph:
    nodes = [
        DependencyNode(node_id="port_murmansk", name="Murmansk", node_type="port", criticality=0.9),
        DependencyNode(node_id="route_nsr", name="NSR", node_type="corridor", criticality=0.9),
        DependencyNode(
            node_id="facility_yamal", name="Yamal LNG", node_type="facility", criticality=0.95
        ),
        DependencyNode(
            node_id="satcom_iridium", name="Iridium", node_type="satcom", criticality=0.8
        ),
    ]
    edges = [
        DependencyEdge(source="satcom_iridium", target="route_nsr", dependency_strength=0.85),
        DependencyEdge(source="port_murmansk", target="route_nsr", dependency_strength=0.9),
        DependencyEdge(source="route_nsr", target="facility_yamal", dependency_strength=0.95),
    ]
    return DependencyGraph(graph_id="arctic-lng", nodes=nodes, edges=edges)


class TestScenarioSimulation:
    def test_correlated_failure_cascade(self) -> None:
        graph = _sample_graph()
        scenario = Scenario(
            scenario_id="arctic-storm-cyber",
            name="Arctic Storm & Cyber Outage",
            events=[
                ScenarioEvent(target="satcom_iridium", state=CorridorState.FUNCTIONALLY_CLOSED),
                ScenarioEvent(target="port_murmansk", state=CorridorState.PHYSICALLY_CLOSED),
            ],
            duration_days=30,
        )
        res = simulate_scenario(scenario, graph)
        assert res.events_applied == 2
        assert len(res.failed_nodes) == 2
        assert "satcom_iridium" in res.failed_nodes
        assert "port_murmansk" in res.failed_nodes
        assert res.total_capacity_loss > 0.4
        assert res.recovery_required is True
        assert len(res.affected_facilities) > 0

    def test_empty_scenario(self) -> None:
        graph = _sample_graph()
        scenario = Scenario(
            scenario_id="baseline",
            name="Baseline",
            events=[],
            duration_days=30,
        )
        res = simulate_scenario(scenario, graph)
        assert res.events_applied == 0
        assert len(res.failed_nodes) == 0
        assert res.total_capacity_loss == 0.0
        assert res.recovery_required is False
