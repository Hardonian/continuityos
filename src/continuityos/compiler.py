from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from continuityos.domain import CompiledPlan, CompileRequest, CorridorFactor, MitigationAction
from continuityos.fusion import FusionPolicy


@dataclass(frozen=True, slots=True)
class _Candidate:
    actions: tuple[MitigationAction, ...]
    cost: float
    continuity: float
    risk: float


class ContinuityCompiler:
    """Deterministic bounded exact compiler for explainable mitigation selection.

    It enumerates feasible action sets up to a configured maximum. This is exact for the
    supplied bounded action set. Larger deployments should use an OR-Tools adapter with
    the same constraints and evidence contract.
    """

    def __init__(self, max_actions: int = 24) -> None:
        self.max_actions = max_actions

    def compile(self, request: CompileRequest) -> CompiledPlan:
        actions = sorted(request.available_actions, key=lambda item: item.action_id)
        if len(actions) > self.max_actions:
            raise ValueError(
                "action count "
                f"{len(actions)} exceeds deterministic compiler limit {self.max_actions}"
            )
        base_continuity = max(0.0, 1.0 - request.assessment.overall_risk)
        best: _Candidate | None = None
        for count in range(0, len(actions) + 1):
            for subset in combinations(actions, count):
                candidate = self._evaluate(request, subset, base_continuity)
                if candidate is None:
                    continue
                if best is None or self._better(
                    candidate, best, request.objective.minimum_continuity
                ):
                    best = candidate

        if best is None:
            return CompiledPlan(
                assessment_id=request.assessment.assessment_id,
                selected_actions=[],
                total_cost=0,
                projected_continuity=base_continuity,
                projected_risk=request.assessment.overall_risk,
                objective_met=False,
                deterministic_solver="bounded-exact-v1",
                approval_required=request.objective.human_approval_required,
                rejected_reason=(
                    "no feasible action set within budget and compatibility constraints"
                ),
            )

        objective_met = best.continuity >= request.objective.minimum_continuity
        return CompiledPlan(
            assessment_id=request.assessment.assessment_id,
            selected_actions=list(best.actions),
            total_cost=round(best.cost, 2),
            projected_continuity=round(best.continuity, 6),
            projected_risk=round(best.risk, 6),
            objective_met=objective_met,
            deterministic_solver="bounded-exact-v1",
            approval_required=request.objective.human_approval_required
            or any(action.requires_human_approval for action in best.actions),
            rejected_reason=(
                None if objective_met else "objective not achievable with available actions"
            ),
        )

    def _evaluate(
        self,
        request: CompileRequest,
        subset: tuple[MitigationAction, ...],
        base_continuity: float,
    ) -> _Candidate | None:
        ids = {action.action_id for action in subset}
        total_cost = sum(action.cost for action in subset)
        if total_cost > request.objective.budget:
            return None
        for action in subset:
            if not action.prerequisites.issubset(ids):
                return None
            if action.incompatible_with.intersection(ids):
                return None
        projected_risk = self._project_risk(request, subset)
        projected_continuity = 1.0 - projected_risk
        return _Candidate(
            actions=subset,
            cost=total_cost,
            continuity=min(1.0, projected_continuity),
            risk=max(0.0, projected_risk),
        )

    @staticmethod
    def _project_risk(request: CompileRequest, subset: tuple[MitigationAction, ...]) -> float:
        factor_risks: dict[CorridorFactor, float] = {
            factor.factor: factor.risk for factor in request.assessment.factors
        }
        if factor_risks:
            weights = FusionPolicy.FACTOR_WEIGHTS
            weight_used = sum(weights[factor] for factor in factor_risks)
            base_factor_risk = (
                sum(factor_risks[factor] * weights[factor] for factor in factor_risks) / weight_used
            )
            non_factor_penalty = max(0.0, request.assessment.overall_risk - base_factor_risk)
            for action in subset:
                for factor, reduction in action.risk_reductions.items():
                    if factor in factor_risks:
                        factor_risks[factor] *= 1.0 - min(0.95, reduction)
            projected_factor_risk = (
                sum(factor_risks[factor] * weights[factor] for factor in factor_risks) / weight_used
            )
            projected_risk = min(1.0, projected_factor_risk + non_factor_penalty)
        else:
            projected_risk = request.assessment.overall_risk

        for action in subset:
            if not action.risk_reductions:
                projected_risk *= 1.0 - min(0.95, action.continuity_gain)
        return max(0.0, min(1.0, projected_risk))

    @staticmethod
    def _better(candidate: _Candidate, incumbent: _Candidate, target: float) -> bool:
        candidate_meets = candidate.continuity >= target
        incumbent_meets = incumbent.continuity >= target
        if candidate_meets != incumbent_meets:
            return candidate_meets
        if candidate_meets:
            candidate_key = (
                candidate.cost,
                -candidate.continuity,
                tuple(action.action_id for action in candidate.actions),
            )
            incumbent_key = (
                incumbent.cost,
                -incumbent.continuity,
                tuple(action.action_id for action in incumbent.actions),
            )
            return candidate_key < incumbent_key
        candidate_key = (
            -candidate.continuity,
            candidate.cost,
            tuple(action.action_id for action in candidate.actions),
        )
        incumbent_key = (
            -incumbent.continuity,
            incumbent.cost,
            tuple(action.action_id for action in incumbent.actions),
        )
        return candidate_key < incumbent_key
