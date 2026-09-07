"""Unit tests for Provider Independence Analyzer."""

from continuityos.graph import DependencyEdge, DependencyGraph, DependencyNode, NodeType
from continuityos.independence import (
    ProviderIndependenceAnalyzer,
)


class TestProviderIndependence:
    """Tests for detecting upstream shared dependencies and false redundancy."""

    def test_truly_independent_providers(self) -> None:
        """Two providers with completely disjoint infrastructure trees."""
        graph = DependencyGraph(
            graph_id="disjoint-net",
            nodes=[
                DependencyNode(
                    node_id="ground-alpha", name="Teleport Alpha", node_type=NodeType.FACILITY
                ),
                DependencyNode(
                    node_id="ground-bravo", name="Teleport Bravo", node_type=NodeType.FACILITY
                ),
                DependencyNode(
                    node_id="prov-alpha", name="Provider Alpha", node_type=NodeType.SATCOM
                ),
                DependencyNode(
                    node_id="prov-bravo", name="Provider Bravo", node_type=NodeType.SATCOM
                ),
            ],
            edges=[
                DependencyEdge(source="ground-alpha", target="prov-alpha"),
                DependencyEdge(source="ground-bravo", target="prov-bravo"),
            ],
        )

        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(
            graph,
            category="satcom",
            provider_node_ids=["prov-alpha", "prov-bravo"],
            minimum_required=2,
        )

        assert res.declared_count == 2
        assert res.independent_count == 2
        assert res.redundancy_valid is True
        assert len(res.shared_dependencies) == 0
        assert "REDUNDANCY VALID" in res.format_text()

    def test_shared_deep_upstream_dependency(self) -> None:
        """Providers share a root power grid / subsea cable two hops upstream."""
        graph = DependencyGraph(
            graph_id="deep-chokepoint-net",
            nodes=[
                DependencyNode(
                    node_id="subsea-backbone",
                    name="Trans-Arctic Subsea Cable",
                    node_type=NodeType.SUBSEA_CABLE,
                ),
                DependencyNode(
                    node_id="gateway-1",
                    name="Coastal Landing Station 1",
                    node_type=NodeType.FACILITY,
                ),
                DependencyNode(
                    node_id="gateway-2",
                    name="Coastal Landing Station 2",
                    node_type=NodeType.FACILITY,
                ),
                DependencyNode(
                    node_id="comm-service-1",
                    name="Regional ISP 1",
                    node_type=NodeType.TERRESTRIAL_NETWORK,
                ),
                DependencyNode(
                    node_id="comm-service-2",
                    name="Regional ISP 2",
                    node_type=NodeType.TERRESTRIAL_NETWORK,
                ),
            ],
            edges=[
                DependencyEdge(source="subsea-backbone", target="gateway-1"),
                DependencyEdge(source="subsea-backbone", target="gateway-2"),
                DependencyEdge(source="gateway-1", target="comm-service-1"),
                DependencyEdge(source="gateway-2", target="comm-service-2"),
            ],
        )

        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(
            graph,
            category="terrestrial_comms",
            provider_node_ids=["comm-service-1", "comm-service-2"],
            minimum_required=2,
        )

        assert res.declared_count == 2
        assert res.independent_count == 1
        assert res.redundancy_valid is False
        assert any(sd.dependency_id == "subsea-backbone" for sd in res.shared_dependencies)
        assert "REDUNDANCY INVALID" in res.format_text()

    def test_attribute_level_shared_chokepoint(self) -> None:
        """Providers share a legal jurisdiction and power grid declared in node attributes."""
        graph = DependencyGraph(
            graph_id="attr-chokepoint-net",
            nodes=[
                DependencyNode(
                    node_id="cloud-east",
                    name="Cloud Hosting East",
                    node_type=NodeType.CLOUD_SERVICE,
                    attributes={"power_grid": "nordic-central-grid", "jurisdiction": "SE"},
                ),
                DependencyNode(
                    node_id="cloud-west",
                    name="Cloud Hosting West",
                    node_type=NodeType.CLOUD_SERVICE,
                    attributes={"power_grid": "nordic-central-grid", "jurisdiction": "SE"},
                ),
            ],
            edges=[],
        )

        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(
            graph,
            category="cloud",
            provider_node_ids=["cloud-east", "cloud-west"],
            minimum_required=2,
        )

        assert res.declared_count == 2
        assert res.independent_count == 1
        assert res.redundancy_valid is False
        assert any("nordic-central-grid" in sd.dependency_id for sd in res.shared_dependencies)

    def test_empty_provider_list(self) -> None:
        """Empty provider list fails safely."""
        graph = DependencyGraph(graph_id="empty-net", nodes=[], edges=[])
        analyzer = ProviderIndependenceAnalyzer()
        res = analyzer.analyze_category(graph, category="navigation", provider_node_ids=[])

        assert res.declared_count == 0
        assert res.independent_count == 0
        assert res.redundancy_valid is False

    def test_holistic_graph_audit(self) -> None:
        """Audit multiple categories simultaneously across a complete graph."""
        graph = DependencyGraph(
            graph_id="full-network-audit",
            nodes=[
                # Comms: shared uplink
                DependencyNode(
                    node_id="uplink-shared",
                    name="Shared Uplink",
                    node_type=NodeType.SATELLITE_UPLINK,
                ),
                DependencyNode(node_id="comms-1", name="Comms 1", node_type=NodeType.SATCOM),
                DependencyNode(node_id="comms-2", name="Comms 2", node_type=NodeType.SATCOM),
                # Suppliers: disjoint
                DependencyNode(node_id="sup-a", name="Supplier A", node_type=NodeType.SUPPLIER),
                DependencyNode(node_id="sup-b", name="Supplier B", node_type=NodeType.SUPPLIER),
            ],
            edges=[
                DependencyEdge(source="uplink-shared", target="comms-1"),
                DependencyEdge(source="uplink-shared", target="comms-2"),
            ],
        )

        analyzer = ProviderIndependenceAnalyzer()
        report = analyzer.analyze_graph(
            graph,
            provider_categories={
                "comms": ["comms-1", "comms-2"],
                "suppliers": ["sup-a", "sup-b"],
            },
        )

        assert report.overall_valid is False  # comms has false redundancy
        assert report.results["comms"].redundancy_valid is False
        assert report.results["suppliers"].redundancy_valid is True

        text = report.format_text()
        assert "PROVIDER INDEPENDENCE & FALSE REDUNDANCY AUDIT" in text
        assert "INVALID" in text
