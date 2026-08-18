"""Tests for Inventory Depletion simulation engine."""

from __future__ import annotations

from continuityos.inventory import (
    InventoryProfile,
    simulate_inventory,
)


class TestInventoryDepletion:
    def test_normal_consumption_with_replenishment(self) -> None:
        profile = InventoryProfile(
            resource_id="fuel-storage",
            name="Heavy Fuel Oil Storage",
            starting_quantity=1000.0,
            unit="metric_tons",
            normal_consumption_per_day=10.0,
            replenishment_per_day=10.0,
            minimum_reserve=200.0,
            critical_threshold=100.0,
        )
        res = simulate_inventory(profile, simulation_days=30)
        assert res.final_quantity == 1000.0
        assert res.days_to_exhaustion is None
        assert res.days_to_critical is None
        assert res.days_to_warning is None
        assert res.final_status == "normal"

    def test_depletion_without_replenishment(self) -> None:
        profile = InventoryProfile(
            resource_id="fuel-storage",
            name="Heavy Fuel Oil Storage",
            starting_quantity=100.0,
            unit="metric_tons",
            normal_consumption_per_day=10.0,
            replenishment_per_day=0.0,
            minimum_reserve=30.0,
            critical_threshold=20.0,
            warning_threshold=45.0,
        )
        res = simulate_inventory(profile, simulation_days=15)
        # Day 0: 100 -> 90
        # Day 5: 50 -> 40 (crosses warning <= 45)
        # Day 8: 20 (crosses critical <= 20)
        # Day 10: 0 (exhausted <= 0)
        assert res.days_to_warning is not None
        assert res.days_to_critical is not None
        assert res.days_to_exhaustion == 9 or res.days_to_exhaustion == 10
        assert res.final_quantity == 0.0
        assert res.final_status == "exhausted"

    def test_substitution_mitigation(self) -> None:
        profile_no_sub = InventoryProfile(
            resource_id="fuel",
            name="Fuel",
            starting_quantity=100.0,
            normal_consumption_per_day=10.0,
            minimum_reserve=20.0,
            critical_threshold=10.0,
        )
        res_no_sub = simulate_inventory(profile_no_sub, simulation_days=10)

        profile_with_sub = InventoryProfile(
            resource_id="fuel",
            name="Fuel",
            starting_quantity=100.0,
            normal_consumption_per_day=10.0,
            substitution_factor=0.5,  # 50% substituted
            minimum_reserve=20.0,
            critical_threshold=10.0,
        )
        res_with_sub = simulate_inventory(profile_with_sub, simulation_days=10)

        assert res_with_sub.final_quantity > res_no_sub.final_quantity
        assert res_with_sub.final_quantity == 50.0
