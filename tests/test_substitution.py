"""Unit tests for Route Substitution Compiler."""

from continuityos.substitution import (
    RouteSubstitutionCandidate,
    compile_route_substitution,
)


class TestRouteSubstitutionCompiler:
    """Tests for multi-dimensional feasibility verification of supply route alternatives."""

    def test_ice_class_deficiency_fails_substitution(self) -> None:
        """Route requires ice reinforcement, but candidate vessel is standard hull."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-ice-fail",
            primary_route_id="corridor/primary-arctic",
            alternative_route_id="corridor/high-latitude-polar",
            route_requires_ice_class=True,
            vessel_ice_class=False,
        )
        res = compile_route_substitution(candidate)
        assert res.geographically_viable is False
        assert res.effective_substitution == "FAIL"
        assert any("ice" in b.lower() for b in res.failure_reasons)

    def test_uninsurable_alternative_fails_substitution(self) -> None:
        """Route is physically clear, but marine underwriters withdraw war-risk coverage."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-insurance-fail",
            primary_route_id="corridor/suez",
            alternative_route_id="corridor/red-sea-alt",
            carrier_available=True,
            insurance_available=False,
        )
        res = compile_route_substitution(candidate)
        assert res.commercially_viable is False
        assert res.effective_substitution == "FAIL"
        assert any("insurance" in b.lower() for b in res.failure_reasons)

    def test_no_carrier_capacity_fails_substitution(self) -> None:
        """Carriers diverted away, zero vessel allocations available."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-carrier-fail",
            primary_route_id="corridor/primary",
            alternative_route_id="corridor/diverted-alt",
            carrier_available=False,
            insurance_available=True,
        )
        res = compile_route_substitution(candidate)
        assert res.commercially_viable is False
        assert res.effective_substitution == "FAIL"
        assert any("carrier" in b.lower() for b in res.failure_reasons)

    def test_inventory_deadline_missed_fails_substitution(self) -> None:
        """Total transit + inland time exceeds critical exhaustion date."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-late-delivery",
            primary_route_id="corridor/fast-sea",
            alternative_route_id="corridor/slow-overland",
            critical_inventory_exhaustion_days=15,
            alternative_transit_days=12,
            inland_rail_days=6,  # 12 + 6 = 18 days > 15 days
        )
        res = compile_route_substitution(candidate)
        assert res.arrival_before_critical_inventory_date is False
        assert res.effective_substitution == "FAIL"
        assert any(
            "exhaustion" in b.lower() or "deadline" in b.lower() for b in res.failure_reasons
        )

    def test_degraded_rail_and_port_capacity(self) -> None:
        """Inland rail is constrained (0.50) and port is tight, yielding DEGRADED effective substitution."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-degraded",
            primary_route_id="corridor/primary",
            alternative_route_id="corridor/congested-bypass",
            quantity_tons=10000.0,
            port_handling_capacity_tons_day=1500.0,  # 1500 < 2000 -> DEGRADED
            inland_rail_capacity_ratio=0.55,  # < 0.70 -> DEGRADED
            critical_inventory_exhaustion_days=40,
            alternative_transit_days=15,
            inland_rail_days=5,
        )
        res = compile_route_substitution(candidate)
        assert res.port_handling_capacity == "DEGRADED"
        assert res.inland_rail_capacity == "DEGRADED"
        assert res.arrival_before_critical_inventory_date is True
        assert res.effective_substitution == "DEGRADED"

    def test_all_constraints_satisfied_passes_substitution(self) -> None:
        """Fully verified alternative route passes all 9 operational layers."""
        candidate = RouteSubstitutionCandidate(
            substitution_id="sub-ideal",
            primary_route_id="Northern Sea Route",
            alternative_route_id="North Atlantic Corridor via Kirkenes",
            cargo_type="aviation_fuel",
            quantity_tons=8000.0,
            critical_inventory_exhaustion_days=35,
            alternative_transit_days=16,
            inland_rail_days=4,  # 20 days < 35 days
            port_handling_capacity_tons_day=5000.0,
            inland_rail_capacity_ratio=1.0,
            vessel_ice_class=True,
            route_requires_ice_class=True,
            carrier_available=True,
            insurance_available=True,
            communications_healthy=True,
            navigation_healthy=True,
            fuel_bunkering_available=True,
            storage_capacity_available=True,
            supplier_available=True,
        )
        res = compile_route_substitution(candidate)
        assert res.geographically_viable is True
        assert res.commercially_viable is True
        assert res.port_handling_capacity == "PASS"
        assert res.inland_rail_capacity == "PASS"
        assert res.arrival_before_critical_inventory_date is True
        assert res.effective_substitution == "PASS"
        assert len(res.failure_reasons) == 0

        report = res.format_report()
        assert "PRIMARY ROUTE:        Northern Sea Route" in report
        assert "Geographically viable:                  YES" in report
        assert "Commercially viable:                    YES" in report
        assert "Port handling capacity:                 PASS" in report
        assert "Inland rail capacity:                   PASS" in report
        assert "Arrival before critical inventory date: YES" in report
        assert "Effective substitution:                 PASS" in report
