"""Test suite for Enterprise & Sovereign Supply Chain and Economic Solvers."""

from __future__ import annotations

from continuityos.supply_chain import (
    BOMComponent,
    EconomicLossCalculator,
    ModalReroutingSolver,
    MultiTierSupplyEngine,
    TransportMode,
)


class TestMultiTierSupplyEngine:
    """Test MultiTierSupplyEngine BOM risk assessment, single sourcing, and lead time."""

    def test_bom_assessment_nominal(self) -> None:
        engine = MultiTierSupplyEngine()
        components = [
            BOMComponent(
                component_id="COMP-01",
                name="Tier 1 Battery Pack",
                tier=1,
                supplier_id="SUP-01",
                is_single_sourced=False,
                lead_time_days=10,
                inventory_buffer_days=30,
                criticality=0.8,
            ),
            BOMComponent(
                component_id="COMP-02",
                name="Tier 2 Cathode Material",
                tier=2,
                supplier_id="SUP-02",
                is_single_sourced=False,
                lead_time_days=15,
                inventory_buffer_days=35,
                criticality=0.7,
            ),
        ]

        assessment = engine.assess_bom("EV-Battery-System", components, corridor_disruption_days=0)
        assert assessment.overall_supply_risk < 0.5
        assert len(assessment.single_source_choke_points) == 0
        assert assessment.critical_shortage_window_days == 30

    def test_bom_assessment_single_source_choke_point(self) -> None:
        engine = MultiTierSupplyEngine()
        components = [
            BOMComponent(
                component_id="COMP-CRITICAL-NICKEL",
                name="Refined High Purity Nickel",
                tier=3,
                supplier_id="MINE-01",
                is_single_sourced=True,
                lead_time_days=25,
                inventory_buffer_days=10,
                criticality=0.95,
            )
        ]

        assessment = engine.assess_bom("High-Purity-Alloy", components, corridor_disruption_days=12)
        assert "COMP-CRITICAL-NICKEL" in assessment.single_source_choke_points
        assert len(assessment.bottlenecks) > 0
        assert assessment.critical_shortage_window_days == 0


class TestEconomicLossCalculator:
    """Test enterprise commercial disruption and financial loss calculations."""

    def test_economic_loss_calculation(self) -> None:
        calc = EconomicLossCalculator()
        estimate = calc.calculate_losses(
            disruption_duration_days=10,
            daily_inventory_value_cad=10_000_000.0,
            vessels_delayed_count=3,
            demurrage_rate_per_vessel_daily_cad=25_000.0,
            production_line_daily_burn_cad=200_000.0,
        )

        assert estimate.disruption_duration_days == 10
        assert estimate.total_demurrage_cost == 750_000.0
        assert estimate.total_production_loss_cost == 2_000_000.0
        assert estimate.total_estimated_loss_cad > 2_750_000.0
        assert "inventory_carrying_cost" in estimate.cost_breakdown_cad


class TestModalReroutingSolver:
    """Test deterministic multi-modal freight rerouting optimizer."""

    def test_modal_rerouting_balanced(self) -> None:
        solver = ModalReroutingSolver()
        result = solver.solve_rerouting(
            corridor_id="VAN-TOR-CORRIDOR",
            origin="Vancouver",
            destination="Toronto",
            distance_km=4350.0,
        )

        assert result.total_options_evaluated >= 4
        assert result.recommended_mode in {
            TransportMode.MARITIME,
            TransportMode.RAIL_CPKC,
            TransportMode.RAIL_CN,
            TransportMode.LONG_HAUL_TRUCK,
        }

    def test_modal_rerouting_time_critical(self) -> None:
        solver = ModalReroutingSolver()
        result = solver.solve_rerouting(
            corridor_id="VAN-TOR-CORRIDOR",
            origin="Vancouver",
            destination="Toronto",
            distance_km=4350.0,
            time_critical=True,
        )

        # Time critical option should be Air Cargo
        assert result.recommended_mode == TransportMode.AIR_CARGO
        assert result.ranked_options[0].mode == TransportMode.AIR_CARGO
