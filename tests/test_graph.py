from continuityos.graph import (
    DependencyEdge,
    DependencyEngine,
    DependencyGraph,
    DependencyNode,
    NodeType,
)


def test_dependency_engine_propagates_cyber_physical_impact() -> None:
    graph = DependencyGraph(
        graph_id="arctic-supply",
        nodes=[
            DependencyNode(
                node_id="idp",
                name="Shared IdP",
                node_type=NodeType.IDENTITY_PROVIDER,
                criticality=0.8,
            ),
            DependencyNode(
                node_id="port-ot", name="Port OT", node_type=NodeType.PORT_OT, criticality=0.9
            ),
            DependencyNode(node_id="port", name="Port", node_type=NodeType.PORT, criticality=1.0),
            DependencyNode(
                node_id="inventory", name="Inventory", node_type=NodeType.INVENTORY, criticality=1.0
            ),
        ],
        edges=[
            DependencyEdge(source="idp", target="port-ot", dependency_strength=0.9),
            DependencyEdge(source="port-ot", target="port", dependency_strength=0.95),
            DependencyEdge(source="port", target="inventory", dependency_strength=0.8),
        ],
    )
    result = DependencyEngine().analyze(graph, {"idp"})
    ids = {item.node_id for item in result.impacted_nodes}
    assert ids == {"idp", "port-ot", "port", "inventory"}
    assert "idp" in result.single_points_of_failure
    assert result.total_weighted_impact > 2.5
