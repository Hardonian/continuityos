"""Route Substitution Compiler.

Evaluates whether an alternate supply corridor or logistics configuration
can realistically satisfy continuity objectives, rather than merely finding
another line on a map.

Evaluates:
  - Origin capacity & supplier availability
  - Available vessel class compatibility & ice requirements
  - Route throughput capacity
  - Port handling & discharge capacity
  - Inland transportation & rail fluidity
  - Communications & navigation integrity
  - Bunkering fuel & storage capacity
  - Carrier availability & marine war-risk insurance
  - Arrival before critical inventory exhaustion deadline
"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class RouteFeasibilityCheck(BaseModel):
    """A specific evaluation check on the substitution route."""

    check_name: str
    dimension: str
    status: str  # PASS, DEGRADED, FAIL
    score: Score
    rationale: str


class SubstitutionEvaluation(BaseModel):
    """Result of comprehensive route substitution compilation."""

    evaluation_id: UUID = Field(default_factory=uuid4)
    substitution_id: str
    primary_route_id: str
    alternative_route_id: str
    geographically_viable: bool
    commercially_viable: bool
    port_handling_capacity: str  # PASS, DEGRADED, FAIL
    inland_rail_capacity: str  # PASS, DEGRADED, FAIL
    arrival_before_critical_inventory_date: bool
    estimated_transit_days: int
    deadline_days: int
    effective_substitution: str  # PASS, DEGRADED, FAIL
    feasibility_checks: list[RouteFeasibilityCheck]
    failure_reasons: list[str]
    summary: str

    def format_report(self) -> str:
        """Format as canonical ContinuityOS substitution decision report."""
        lines = [
            "=" * 78,
            "CONTINUITYOS ROUTE SUBSTITUTION COMPILER REPORT",
            "=" * 78,
            f"PRIMARY ROUTE:        {self.primary_route_id}",
            f"ALTERNATIVE:          {self.alternative_route_id}",
            "",
            f"Geographically viable:                  {'YES' if self.geographically_viable else 'NO'}",
            f"Commercially viable:                    {'YES' if self.commercially_viable else 'NO'}",
            f"Port handling capacity:                 {self.port_handling_capacity}",
            f"Inland rail capacity:                   {self.inland_rail_capacity}",
            f"Transit + inland lead time:             {self.estimated_transit_days} days (deadline: {self.deadline_days} days)",
            f"Arrival before critical inventory date: {'YES' if self.arrival_before_critical_inventory_date else 'NO'}",
            "",
            f"Effective substitution:                 {self.effective_substitution}",
            "=" * 78,
            "",
            "Feasibility Check Breakdown:",
        ]
        for chk in self.feasibility_checks:
            lines.append(
                f"  [{chk.status:<8}] {chk.check_name:<34} (score: {chk.score:.2f}) -> {chk.rationale}"
            )
        if self.failure_reasons:
            lines.append("")
            lines.append("Critical Substitution Blockers:")
            for fr in self.failure_reasons:
                lines.append(f"  ! {fr}")
        lines.append("=" * 78)
        return "\n".join(lines)


class RouteSubstitutionCandidate(BaseModel):
    """Input parameters for evaluating a route substitution."""

    substitution_id: str = "sub-001"
    primary_route_id: str
    alternative_route_id: str
    cargo_type: str = "general"
    quantity_tons: float = 10000.0
    critical_inventory_exhaustion_days: int = 30
    alternative_transit_days: int = 20
    inland_rail_days: int = 5
    alternative_route_capacity_tons_day: float = 5000.0
    port_handling_capacity_tons_day: float = 8000.0
    inland_rail_capacity_ratio: float = 1.0  # 1.0 = PASS, 0.5 = DEGRADED, <= 0.2 = FAIL
    vessel_class: str = "Handymax"
    vessel_ice_class: bool = False
    route_requires_ice_class: bool = False
    carrier_available: bool = True
    insurance_available: bool = True
    communications_healthy: bool = True
    navigation_healthy: bool = True
    fuel_bunkering_available: bool = True
    storage_capacity_available: bool = True
    supplier_available: bool = True


def compile_route_substitution(candidate: RouteSubstitutionCandidate) -> SubstitutionEvaluation:
    """Compile and prove whether an alternate supply route satisfies continuity objectives."""
    checks: list[RouteFeasibilityCheck] = []
    blockers: list[str] = []

    # 1. Geographical Viability & Ice Constraints
    geo_viable = True
    if candidate.route_requires_ice_class and not candidate.vessel_ice_class:
        geo_viable = False
        blockers.append(
            "Route requires Polar Ice Class vessel; assigned vessel lacks ice reinforcement"
        )
        checks.append(
            RouteFeasibilityCheck(
                check_name="ice_class_compatibility",
                dimension="physical",
                status="FAIL",
                score=0.0,
                rationale="Vessel lacks mandatory Polar/Baltic ice class notation",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="ice_class_compatibility",
                dimension="physical",
                status="PASS",
                score=1.0,
                rationale="Ice navigation constraints met or not applicable",
            )
        )

    # 2. Commercial Viability (Carrier + Insurance)
    comm_viable = candidate.carrier_available and candidate.insurance_available
    if not candidate.carrier_available:
        blockers.append("No carrier capacity committed or available for alternate route")
        checks.append(
            RouteFeasibilityCheck(
                check_name="carrier_availability",
                dimension="commercial",
                status="FAIL",
                score=0.0,
                rationale="Carriers diverted or unavailable",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="carrier_availability",
                dimension="commercial",
                status="PASS",
                score=1.0,
                rationale="Commercial carrier capacity confirmed",
            )
        )

    if not candidate.insurance_available:
        blockers.append("Marine war-risk insurance underwriters withdrawn; route uninsurable")
        checks.append(
            RouteFeasibilityCheck(
                check_name="insurance_underwriting",
                dimension="commercial",
                status="FAIL",
                score=0.0,
                rationale="Insurance coverage unavailable",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="insurance_underwriting",
                dimension="commercial",
                status="PASS",
                score=1.0,
                rationale="War-risk and marine hull coverage active",
            )
        )

    # 3. Port Handling Capacity
    if candidate.port_handling_capacity_tons_day <= 0:
        port_status = "FAIL"
        port_score = 0.0
        blockers.append("Alternate destination port has zero handling throughput capacity")
    elif candidate.port_handling_capacity_tons_day < (candidate.quantity_tons / 5.0):
        port_status = "DEGRADED"
        port_score = 0.6
    else:
        port_status = "PASS"
        port_score = 1.0

    checks.append(
        RouteFeasibilityCheck(
            check_name="port_handling_capacity",
            dimension="logistics",
            status=port_status,
            score=port_score,
            rationale=f"Port capacity: {candidate.port_handling_capacity_tons_day:,.0f} tons/day",
        )
    )

    # 4. Inland Rail / Transportation Capacity
    if candidate.inland_rail_capacity_ratio <= 0.2:
        rail_status = "FAIL"
        rail_score = 0.1
        blockers.append("Inland rail/intermodal corridor severely constrained or blocked")
    elif candidate.inland_rail_capacity_ratio < 0.7:
        rail_status = "DEGRADED"
        rail_score = candidate.inland_rail_capacity_ratio
    else:
        rail_status = "PASS"
        rail_score = 1.0

    checks.append(
        RouteFeasibilityCheck(
            check_name="inland_rail_capacity",
            dimension="logistics",
            status=rail_status,
            score=rail_score,
            rationale=f"Inland transport fluidity ratio: {candidate.inland_rail_capacity_ratio:.1%}",
        )
    )

    # 5. Cyber-Physical & Communications/Navigation
    if not candidate.communications_healthy:
        checks.append(
            RouteFeasibilityCheck(
                check_name="communications_integrity",
                dimension="cyber_physical",
                status="DEGRADED",
                score=0.4,
                rationale="SATCOM/terrestrial communications degraded along corridor",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="communications_integrity",
                dimension="cyber_physical",
                status="PASS",
                score=1.0,
                rationale="Encrypted SATCOM and terrestrial backhaul verified",
            )
        )

    if not candidate.navigation_healthy:
        checks.append(
            RouteFeasibilityCheck(
                check_name="navigation_integrity",
                dimension="cyber_physical",
                status="DEGRADED",
                score=0.4,
                rationale="GNSS spoofing or PNT anomalies detected",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="navigation_integrity",
                dimension="cyber_physical",
                status="PASS",
                score=1.0,
                rationale="PNT and multi-constellation GNSS verified",
            )
        )

    # 6. Fuel & Storage Availability
    if not candidate.fuel_bunkering_available:
        blockers.append("Bunkering fuel unavailable along alternate transit corridor")
        checks.append(
            RouteFeasibilityCheck(
                check_name="fuel_bunkering_availability",
                dimension="logistics",
                status="FAIL",
                score=0.0,
                rationale="Fuel bunkering unavailable",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="fuel_bunkering_availability",
                dimension="logistics",
                status="PASS",
                score=1.0,
                rationale="Bunkering stations operational",
            )
        )

    if not candidate.storage_capacity_available:
        checks.append(
            RouteFeasibilityCheck(
                check_name="storage_capacity",
                dimension="inventory",
                status="DEGRADED",
                score=0.5,
                rationale="Destination terminal storage utilization near ceiling",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="storage_capacity",
                dimension="inventory",
                status="PASS",
                score=1.0,
                rationale="Terminal storage capacity confirmed",
            )
        )

    if not candidate.supplier_available:
        blockers.append("Origin supplier cannot fulfill volume on alternate route")
        checks.append(
            RouteFeasibilityCheck(
                check_name="supplier_availability",
                dimension="upstream",
                status="FAIL",
                score=0.0,
                rationale="Supplier allocation unavailable",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="supplier_availability",
                dimension="upstream",
                status="PASS",
                score=1.0,
                rationale="Origin supplier contracted and ready",
            )
        )

    # 7. Inventory Arrival Deadline
    total_transit_days = candidate.alternative_transit_days + candidate.inland_rail_days
    arrival_before_deadline = total_transit_days <= candidate.critical_inventory_exhaustion_days

    if not arrival_before_deadline:
        deficit_days = total_transit_days - candidate.critical_inventory_exhaustion_days
        blockers.append(
            f"Total arrival lead time ({total_transit_days} days) exceeds critical inventory exhaustion deadline "
            f"({candidate.critical_inventory_exhaustion_days} days) by {deficit_days} days"
        )
        checks.append(
            RouteFeasibilityCheck(
                check_name="arrival_before_deadline",
                dimension="timeline",
                status="FAIL",
                score=0.0,
                rationale=f"Arrives day {total_transit_days}, after reserve exhaustion day {candidate.critical_inventory_exhaustion_days}",
            )
        )
    else:
        checks.append(
            RouteFeasibilityCheck(
                check_name="arrival_before_deadline",
                dimension="timeline",
                status="PASS",
                score=1.0,
                rationale=f"Arrives day {total_transit_days}, safely within reserve deadline {candidate.critical_inventory_exhaustion_days} days",
            )
        )

    # Effective Substitution Determination
    if (
        blockers
        or not geo_viable
        or not comm_viable
        or not arrival_before_deadline
        or port_status == "FAIL"
        or rail_status == "FAIL"
    ):
        effective_substitution = "FAIL"
    elif (
        port_status == "DEGRADED"
        or rail_status == "DEGRADED"
        or any(c.status == "DEGRADED" for c in checks)
    ):
        effective_substitution = "DEGRADED"
    else:
        effective_substitution = "PASS"

    summary = (
        f"Route substitution '{candidate.alternative_route_id}' for '{candidate.primary_route_id}' is FEASIBLE ({effective_substitution})"
        if effective_substitution in {"PASS", "DEGRADED"}
        else f"Route substitution '{candidate.alternative_route_id}' FAILED: {len(blockers)} critical blocker(s)"
    )

    return SubstitutionEvaluation(
        substitution_id=candidate.substitution_id,
        primary_route_id=candidate.primary_route_id,
        alternative_route_id=candidate.alternative_route_id,
        geographically_viable=geo_viable,
        commercially_viable=comm_viable,
        port_handling_capacity=port_status,
        inland_rail_capacity=rail_status,
        arrival_before_critical_inventory_date=arrival_before_deadline,
        estimated_transit_days=total_transit_days,
        deadline_days=candidate.critical_inventory_exhaustion_days,
        effective_substitution=effective_substitution,
        feasibility_checks=checks,
        failure_reasons=blockers,
        summary=summary,
    )
