"""Defense Readiness Reporting System (DRRS) & NATO C-Level Readiness Engine.

Maps supply network reconciliation, strategic inventory thresholds, and functional
corridor closure states directly into standardized defense readiness metrics.

Readiness Scale:
  C-1: Fully Mission Capable (>=95% continuity, >=30 days reserve, 0 critical SPOFs)
  C-2: Substantially Mission Capable (80-94% continuity, 20-29 days reserve, minor drift)
  C-3: Marginally Mission Capable (65-79% continuity, 10-19 days reserve, degraded comms/nav)
  C-4: Not Mission Capable (<65% continuity, <10 days reserve, or critical corridor closed)
  C-5: Overhaul / Strategic Regeneration (Restoration underway)
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import CorridorState, Score
from continuityos.policy import PolicyEvaluation
from continuityos.reconcile import ReconciliationResult, ReconciliationStatus


class CLevelRating(StrEnum):
    C1_FULLY_MISSION_CAPABLE = "C-1_fully_capable"
    C2_SUBSTANTIALLY_CAPABLE = "C-2_substantially_capable"
    C3_MARGINALLY_CAPABLE = "C-3_marginally_capable"
    C4_NOT_MISSION_CAPABLE = "C-4_not_capable"
    C5_REGENERATION_UNDERWAY = "C-5_regeneration"


class MissionLimitingFactor(BaseModel):
    """A specific supply, corridor, or cyber constraint limiting mission readiness."""

    factor_id: str
    category: str  # "CORRIDOR_STATE", "INVENTORY_SHORTAGE", "POLICY_VIOLATION", "COMMUNICATIONS"
    description: str
    impact_on_c_rating: str


class ReadinessAssessment(BaseModel):
    """Complete Defense Readiness Assessment packet."""

    assessment_id: UUID = Field(default_factory=uuid4)
    unit_or_theater_id: str
    c_rating: CLevelRating
    overall_continuity_score: Score
    inventory_readiness_score: Score
    corridor_operational_score: Score
    mission_limiting_factors: list[MissionLimitingFactor] = Field(default_factory=list)
    executive_briefing: str


class ReadinessEngine:
    """Calculates standardized defense readiness ratings from supply network telemetry."""

    def evaluate_readiness(
        self,
        theater_id: str,
        *,
        overall_continuity: float,
        inventory_reserve_days: float,
        corridor_state: CorridorState = CorridorState.OPEN,
        policy_result: PolicyEvaluation | None = None,
        reconciliation_result: ReconciliationResult | None = None,
    ) -> ReadinessAssessment:
        limiting_factors: list[MissionLimitingFactor] = []

        # 1. Corridor State impact
        corridor_score = 1.0
        if corridor_state in {CorridorState.PHYSICALLY_CLOSED, CorridorState.FUNCTIONALLY_CLOSED}:
            corridor_score = 0.0
            limiting_factors.append(
                MissionLimitingFactor(
                    factor_id="CORRIDOR_CLOSED",
                    category="CORRIDOR_STATE",
                    description=f"Primary theater transit corridor is {corridor_state}",
                    impact_on_c_rating="Direct downgrade to C-4",
                )
            )
        elif corridor_state in {
            CorridorState.OPEN_BUT_UNINSURABLE,
            CorridorState.OPEN_BUT_NO_CARRIER_CAPACITY,
            CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED,
            CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED,
        }:
            corridor_score = 0.50
            limiting_factors.append(
                MissionLimitingFactor(
                    factor_id="CORRIDOR_DEGRADED",
                    category="CORRIDOR_STATE",
                    description=f"Corridor is {corridor_state}",
                    impact_on_c_rating="Restricts rating to C-3 maximum",
                )
            )
        elif corridor_state in {
            CorridorState.OPEN_DEGRADED,
            CorridorState.OPEN_CAPACITY_CONSTRAINED,
        }:
            corridor_score = 0.80

        # 2. Inventory score (target = 30 days)
        inventory_score = min(1.0, inventory_reserve_days / 30.0)
        if inventory_reserve_days < 7:
            limiting_factors.append(
                MissionLimitingFactor(
                    factor_id="CRITICAL_INVENTORY_DEPLETION",
                    category="INVENTORY_SHORTAGE",
                    description=(
                        f"Strategic reserves down to {inventory_reserve_days:.1f} days (< 7d)"
                    ),
                    impact_on_c_rating="Direct downgrade to C-4",
                )
            )
        elif inventory_reserve_days < 20:
            limiting_factors.append(
                MissionLimitingFactor(
                    factor_id="LOW_INVENTORY_RESERVE",
                    category="INVENTORY_SHORTAGE",
                    description=(
                        f"Strategic reserves down to {inventory_reserve_days:.1f} days (< 20d)"
                    ),
                    impact_on_c_rating="Restricts rating to C-2/C-3",
                )
            )

        # 3. Policy & Reconciliation impact
        if (
            reconciliation_result
            and reconciliation_result.overall_status == ReconciliationStatus.FAIL
        ):
            limiting_factors.append(
                MissionLimitingFactor(
                    factor_id="POLICY_RECONCILIATION_FAILURE",
                    category="POLICY_VIOLATION",
                    description=(
                        f"{reconciliation_result.fail_count} critical policy assertions failing"
                    ),
                    impact_on_c_rating="Restricts rating to C-3 or C-4",
                )
            )

        # 4. Synthesize final C-Level Rating
        if corridor_score == 0.0 or inventory_reserve_days < 7 or overall_continuity < 0.65:
            c_rating = CLevelRating.C4_NOT_MISSION_CAPABLE
        elif (
            corridor_score <= 0.50
            or inventory_reserve_days < 20
            or overall_continuity < 0.80
            or (
                reconciliation_result
                and reconciliation_result.overall_status == ReconciliationStatus.FAIL
            )
        ):
            c_rating = CLevelRating.C3_MARGINALLY_CAPABLE
        elif inventory_reserve_days < 30 or overall_continuity < 0.95:
            c_rating = CLevelRating.C2_SUBSTANTIALLY_CAPABLE
        else:
            c_rating = CLevelRating.C1_FULLY_MISSION_CAPABLE

        briefing_parts = [
            f"Theater Readiness Assessment: {c_rating.value.upper()}",
            f"Continuity: {overall_continuity:.1%}",
            f"Inventory Reserves: {inventory_reserve_days:.1f} days",
            f"Corridor Operational Status: {corridor_state.value}",
        ]
        if limiting_factors:
            briefing_parts.append(
                f"{len(limiting_factors)} Mission-Limiting Factors Active: "
                + "; ".join(f.description for f in limiting_factors)
            )

        return ReadinessAssessment(
            unit_or_theater_id=theater_id,
            c_rating=c_rating,
            overall_continuity_score=round(overall_continuity, 4),
            inventory_readiness_score=round(inventory_score, 4),
            corridor_operational_score=round(corridor_score, 4),
            mission_limiting_factors=limiting_factors,
            executive_briefing=" | ".join(briefing_parts),
        )
