"""Assurance Budgeting Engine.

Quantifies how much independent capacity, evidence, trust, redundancy,
and recovery margin a supply chain or critical corridor must possess before
it is considered compliant. Produces a multi-dimensional scorecard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score
from continuityos.dsl import AssurancePolicySpec


class AssuranceDimensionResult(BaseModel):
    """Result of evaluating a single assurance dimension."""

    dimension: str
    category: str  # objective, tolerance, evidence, commercial, inventory, recovery
    passed: bool
    required: str
    observed: str
    score: Score
    message: str


class AssuranceScorecard(BaseModel):
    """Complete multi-dimensional assurance scorecard."""

    scorecard_id: UUID = Field(default_factory=uuid4)
    policy_name: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_compliant: bool
    assurance_score: Score
    dimensions: list[AssuranceDimensionResult]
    failed_dimensions: list[str]
    summary: str

    def format_table(self) -> str:
        """Format the scorecard as a clean human-readable table."""
        lines = [
            "=" * 78,
            f"ASSURANCE BUDGET SCORECARD — {self.policy_name}",
            "=" * 78,
            f"Overall Status:   {'COMPLIANT' if self.overall_compliant else 'NON-COMPLIANT'}",
            f"Assurance Score:  {self.assurance_score:.1%}",
            f"Evaluated At:     {self.evaluated_at.isoformat()}",
            "",
            f"{'CATEGORY':<14} {'DIMENSION':<28} {'STATUS':<8} {'REQUIRED':<12} {'OBSERVED':<10}",
            "-" * 78,
        ]
        for dim in self.dimensions:
            status = "PASS" if dim.passed else "FAIL"
            lines.append(
                f"{dim.category.upper():<14} {dim.dimension:<28} {status:<8} {dim.required:<12} {dim.observed:<10}"
            )
        lines.append("-" * 78)
        if self.failed_dimensions:
            lines.append(f"Failed Dimensions ({len(self.failed_dimensions)}):")
            for fd in self.failed_dimensions:
                lines.append(f"  * {fd}")
        else:
            lines.append("All declared assurance constraints satisfied.")
        lines.append("=" * 78)
        return "\n".join(lines)


class AssuranceObservedState(BaseModel):
    """Observed network and supply state for assurance budgeting."""

    continuity_score: float = 1.0
    available_corridors: int = 2
    available_ports: int = 2
    independent_comm_providers: int = 2
    independent_nav_sources: int = 3
    independent_obs_sources: int = 2
    independent_operational_sources: int = 2
    independent_environmental_sources: int = 2
    carrier_options: int = 2
    insurance_verified: bool = True
    reserve_days: float = 45.0
    assured_replenishment_cycles: int = 1
    carrier_return_verified: bool = True
    backlog_clearance_verified: bool = True
    reserve_restoration_verified: bool = True


def evaluate_assurance(
    policy: AssurancePolicySpec,
    state: AssuranceObservedState,
    policy_name: str = "assurance-policy",
) -> AssuranceScorecard:
    """Evaluate an AssurancePolicy against observed supply network state."""
    dimensions: list[AssuranceDimensionResult] = []

    # 1. Continuity Objective
    req_cont = policy.continuity_objective.minimum
    obs_cont = state.continuity_score
    cont_pass = obs_cont >= req_cont
    dimensions.append(
        AssuranceDimensionResult(
            dimension="continuity_objective",
            category="objective",
            passed=cont_pass,
            required=f">= {req_cont:.1%}",
            observed=f"{obs_cont:.1%}",
            score=min(1.0, obs_cont / req_cont) if req_cont > 0 else 1.0,
            message="Satisfies minimum continuity objective"
            if cont_pass
            else f"Continuity deficit: {req_cont - obs_cont:.1%}",
        )
    )

    # 2. Failure Tolerance
    # Corridor loss tolerance (requires at least tolerate + 1 available)
    req_corr = policy.tolerate.corridor_loss + 1
    obs_corr = state.available_corridors
    corr_pass = obs_corr >= req_corr
    dimensions.append(
        AssuranceDimensionResult(
            dimension="corridor_redundancy",
            category="tolerance",
            passed=corr_pass,
            required=f">= {req_corr} corridors",
            observed=f"{obs_corr}",
            score=min(1.0, obs_corr / req_corr) if req_corr > 0 else 1.0,
            message=f"Tolerates {policy.tolerate.corridor_loss} corridor loss"
            if corr_pass
            else f"Requires {req_corr - obs_corr} additional corridor(s)",
        )
    )

    # Port loss tolerance
    req_ports = policy.tolerate.port_loss + 1
    obs_ports = state.available_ports
    ports_pass = obs_ports >= req_ports
    dimensions.append(
        AssuranceDimensionResult(
            dimension="port_redundancy",
            category="tolerance",
            passed=ports_pass,
            required=f">= {req_ports} ports",
            observed=f"{obs_ports}",
            score=min(1.0, obs_ports / req_ports) if req_ports > 0 else 1.0,
            message=f"Tolerates {policy.tolerate.port_loss} port loss"
            if ports_pass
            else f"Requires {req_ports - obs_ports} additional port(s)",
        )
    )

    # Comm provider loss tolerance
    req_comm = policy.tolerate.communication_provider_loss + 1
    obs_comm = state.independent_comm_providers
    comm_pass = obs_comm >= req_comm
    dimensions.append(
        AssuranceDimensionResult(
            dimension="communication_tolerance",
            category="tolerance",
            passed=comm_pass,
            required=f">= {req_comm} providers",
            observed=f"{obs_comm}",
            score=min(1.0, obs_comm / req_comm) if req_comm > 0 else 1.0,
            message=f"Tolerates {policy.tolerate.communication_provider_loss} comm loss"
            if comm_pass
            else f"Requires {req_comm - obs_comm} additional independent provider(s)",
        )
    )

    # Navigation loss tolerance
    req_nav = policy.tolerate.navigation_source_loss + 1
    obs_nav = state.independent_nav_sources
    nav_pass = obs_nav >= req_nav
    dimensions.append(
        AssuranceDimensionResult(
            dimension="navigation_tolerance",
            category="tolerance",
            passed=nav_pass,
            required=f">= {req_nav} sources",
            observed=f"{obs_nav}",
            score=min(1.0, obs_nav / req_nav) if req_nav > 0 else 1.0,
            message=f"Tolerates {policy.tolerate.navigation_source_loss} nav source loss"
            if nav_pass
            else f"Requires {req_nav - obs_nav} additional navigation source(s)",
        )
    )

    # 3. Evidence Independence
    req_ev_ops = policy.evidence.minimum_independent_operational_sources
    obs_ev_ops = state.independent_operational_sources
    ev_ops_pass = obs_ev_ops >= req_ev_ops
    dimensions.append(
        AssuranceDimensionResult(
            dimension="operational_evidence_sources",
            category="evidence",
            passed=ev_ops_pass,
            required=f">= {req_ev_ops} sources",
            observed=f"{obs_ev_ops}",
            score=min(1.0, obs_ev_ops / req_ev_ops) if req_ev_ops > 0 else 1.0,
            message="Satisfies operational source diversity"
            if ev_ops_pass
            else f"Needs {req_ev_ops - obs_ev_ops} more independent operational source(s)",
        )
    )

    req_ev_env = policy.evidence.minimum_independent_environmental_sources
    obs_ev_env = state.independent_environmental_sources
    ev_env_pass = obs_ev_env >= req_ev_env
    dimensions.append(
        AssuranceDimensionResult(
            dimension="environmental_evidence_sources",
            category="evidence",
            passed=ev_env_pass,
            required=f">= {req_ev_env} sources",
            observed=f"{obs_ev_env}",
            score=min(1.0, obs_ev_env / req_ev_env) if req_ev_env > 0 else 1.0,
            message="Satisfies environmental source diversity"
            if ev_env_pass
            else f"Needs {req_ev_env - obs_ev_env} more independent environmental source(s)",
        )
    )

    # 4. Commercial Assurance
    req_car = policy.commercial.minimum_carrier_options
    obs_car = state.carrier_options
    car_pass = obs_car >= req_car
    dimensions.append(
        AssuranceDimensionResult(
            dimension="carrier_options",
            category="commercial",
            passed=car_pass,
            required=f">= {req_car} carriers",
            observed=f"{obs_car}",
            score=min(1.0, obs_car / req_car) if req_car > 0 else 1.0,
            message="Sufficient commercial carrier competition"
            if car_pass
            else f"Requires {req_car - obs_car} additional commercial carrier option(s)",
        )
    )

    if policy.commercial.insurance_required:
        ins_pass = state.insurance_verified
        dimensions.append(
            AssuranceDimensionResult(
                dimension="insurance_underwriting",
                category="commercial",
                passed=ins_pass,
                required="true",
                observed="true" if ins_pass else "false",
                score=1.0 if ins_pass else 0.0,
                message="War-risk and marine insurance coverage active"
                if ins_pass
                else "Insurance coverage withdrawn or unverified",
            )
        )

    # 5. Strategic Inventory
    req_inv = policy.inventory.minimum_reserve_days
    obs_inv = state.reserve_days
    inv_pass = obs_inv >= req_inv
    dimensions.append(
        AssuranceDimensionResult(
            dimension="inventory_reserve_days",
            category="inventory",
            passed=inv_pass,
            required=f">= {req_inv} days",
            observed=f"{obs_inv:.1f} days",
            score=min(1.0, obs_inv / req_inv) if req_inv > 0 else 1.0,
            message="Strategic reserve days satisfy buffer"
            if inv_pass
            else f"Reserve deficit of {req_inv - obs_inv:.1f} days",
        )
    )

    req_cycles = policy.inventory.minimum_assured_replenishment_cycles
    obs_cycles = state.assured_replenishment_cycles
    cycles_pass = obs_cycles >= req_cycles
    dimensions.append(
        AssuranceDimensionResult(
            dimension="assured_replenishment_cycles",
            category="inventory",
            passed=cycles_pass,
            required=f">= {req_cycles} cycle(s)",
            observed=f"{obs_cycles}",
            score=min(1.0, obs_cycles / req_cycles) if req_cycles > 0 else 1.0,
            message="Next replenishment cycle assured"
            if cycles_pass
            else "Replenishment cycle unverified or disrupted",
        )
    )

    # 6. Recovery Verification
    if policy.recovery.verify_carrier_return:
        cr_pass = state.carrier_return_verified
        dimensions.append(
            AssuranceDimensionResult(
                dimension="recovery_carrier_return",
                category="recovery",
                passed=cr_pass,
                required="verified",
                observed="verified" if cr_pass else "unverified",
                score=1.0 if cr_pass else 0.0,
                message="Carrier return contractually or physically verified"
                if cr_pass
                else "Carrier return not yet confirmed",
            )
        )

    if policy.recovery.verify_backlog_clearance:
        bl_pass = state.backlog_clearance_verified
        dimensions.append(
            AssuranceDimensionResult(
                dimension="recovery_backlog_clearance",
                category="recovery",
                passed=bl_pass,
                required="verified",
                observed="verified" if bl_pass else "backlog_active",
                score=1.0 if bl_pass else 0.0,
                message="Port and transit backlogs confirmed cleared"
                if bl_pass
                else "Active backlog prevents full restoration",
            )
        )

    if policy.recovery.verify_reserve_restoration:
        res_pass = state.reserve_restoration_verified
        dimensions.append(
            AssuranceDimensionResult(
                dimension="recovery_reserve_restoration",
                category="recovery",
                passed=res_pass,
                required="verified",
                observed="verified" if res_pass else "depleted",
                score=1.0 if res_pass else 0.0,
                message="Strategic reserves confirmed rebuilt to baseline"
                if res_pass
                else "Reserves still recovering toward nominal buffer",
            )
        )

    # Calculate overall compliance and score
    failed = [dim.dimension for dim in dimensions if not dim.passed]
    total_score = sum(dim.score for dim in dimensions) / len(dimensions) if dimensions else 0.0
    overall_compliant = len(failed) == 0

    summary = (
        f"Assurance policy '{policy_name}' COMPLIANT ({total_score:.1%})"
        if overall_compliant
        else f"Assurance policy '{policy_name}' NON-COMPLIANT: {len(failed)} dimension(s) failed ({', '.join(failed)})"
    )

    return AssuranceScorecard(
        policy_name=policy_name,
        overall_compliant=overall_compliant,
        assurance_score=round(total_score, 4),
        dimensions=dimensions,
        failed_dimensions=failed,
        summary=summary,
    )
