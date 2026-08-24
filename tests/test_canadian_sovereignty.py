"""Test suite for Canadian Sovereign Security, Protected B/C, and Strategic Corridors."""

from __future__ import annotations

from continuityos.domain import DataClassification
from continuityos.graph import (
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    DependencyNode,
    NodeType,
)
from continuityos.sovereign import SecurityLabel


class TestCanadianSecurityClassification:
    """Test Canadian Federal Government security markings and clearance rankings."""

    def test_canadian_protected_levels(self) -> None:
        assert DataClassification.UNCLASSIFIED.level == 0
        assert DataClassification.PROTECTED_A.level == 1
        assert DataClassification.PROTECTED_B.level == 2
        assert DataClassification.PROTECTED_C.level == 3
        assert DataClassification.CONFIDENTIAL.level == 3
        assert DataClassification.SECRET.level == 4
        assert DataClassification.TOP_SECRET.level == 5
        assert DataClassification.COSMIC_TOP_SECRET.level == 6

    def test_protected_b_access_boundary(self) -> None:
        protected_b_label = SecurityLabel(
            classification=DataClassification.PROTECTED_B,
            owner_nation="CAN",
        )

        # Canadian with Protected B or higher -> Authorized
        assert protected_b_label.is_authorized(DataClassification.PROTECTED_B, "CAN", set()) is True
        assert protected_b_label.is_authorized(DataClassification.SECRET, "CAN", set()) is True

        # Canadian with Unclassified clearance -> Denied
        assert (
            protected_b_label.is_authorized(DataClassification.UNCLASSIFIED, "CAN", set()) is False
        )

    def test_canadian_eyes_only_dissemination(self) -> None:
        ceo_label = SecurityLabel(
            classification=DataClassification.SECRET,
            dissemination_controls={"CANADIAN_EYES_ONLY"},
            owner_nation="CAN",
        )

        # Canadian citizen with SECRET clearance -> Authorized
        assert ceo_label.is_authorized(DataClassification.SECRET, "CAN", set()) is True

        # US ally with SECRET clearance -> Denied due to Canadian Eyes Only
        assert ceo_label.is_authorized(DataClassification.SECRET, "USA", set()) is False

    def test_can_us_fvey_dissemination(self) -> None:
        fvey_label = SecurityLabel(
            classification=DataClassification.SECRET,
            dissemination_controls={"CAN_US_FVEY"},
            owner_nation="CAN",
        )

        assert fvey_label.is_authorized(DataClassification.SECRET, "CAN", set()) is True
        assert fvey_label.is_authorized(DataClassification.SECRET, "USA", set()) is True
        assert fvey_label.is_authorized(DataClassification.SECRET, "GBR", set()) is True
        assert fvey_label.is_authorized(DataClassification.SECRET, "FRA", set()) is False


class TestSupplyChainGraphExtensions:
    """Test new supply chain node types and Canadian strategic mineral topologies."""

    def test_critical_minerals_graph_creation(self) -> None:
        nodes = [
            DependencyNode(
                node_id="MINE-01", name="Ring of Fire Mine", node_type=NodeType.MINE_OR_REFINERY
            ),
            DependencyNode(
                node_id="SMELT-02", name="Sudbury Smelter", node_type=NodeType.MINE_OR_REFINERY
            ),
            DependencyNode(node_id="RAIL-03", name="CN Rail Hub", node_type=NodeType.RAIL_HUB),
            DependencyNode(
                node_id="PLANT-04",
                name="Windsor Gigafactory",
                node_type=NodeType.MANUFACTURING_PLANT,
            ),
            DependencyNode(node_id="PORT-05", name="Montreal Port", node_type=NodeType.PORT),
        ]
        edges = [
            DependencyEdge(source="MINE-01", target="SMELT-02", kind=DependencyKind.REFINES),
            DependencyEdge(source="SMELT-02", target="RAIL-03", kind=DependencyKind.TRANSPORTS),
            DependencyEdge(source="RAIL-03", target="PLANT-04", kind=DependencyKind.MANUFACTURES),
            DependencyEdge(source="RAIL-03", target="PORT-05", kind=DependencyKind.TRANSPORTS),
        ]

        graph = DependencyGraph(graph_id="can-critical-minerals-test", nodes=nodes, edges=edges)
        assert len(graph.nodes) == 5
        assert len(graph.edges) == 4
