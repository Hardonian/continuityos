"""Enterprise and Canadian Sovereign Multi-Tier Supply Chain Engine.

Provides:
  1. MultiTierSupplyEngine: Evaluates multi-tier BOM risk and single-source choke points.
  2. EconomicLossCalculator: Calculates demurrage penalties and plant idling stoppage costs.
  3. ModalReroutingSolver: Deterministic multi-modal routing optimizer (Rail/Maritime/Road/Air).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class TransportMode(StrEnum):
    MARITIME = "maritime"
    RAIL_CPKC = "rail_cpkc"
    RAIL_CN = "rail_cn"
    LONG_HAUL_TRUCK = "long_haul_truck"
    AIR_CARGO = "air_cargo"


class BOMComponent(BaseModel):
    """Component or raw material specification in a multi-tier supply network."""

    component_id: str
    name: str
    tier: int = Field(ge=1, le=3)  # 1 = Direct Tier-1, 2 = Sub-tier, 3 = Raw/Refined Material
    supplier_id: str
    origin_country: str = "CAN"
    is_single_sourced: bool = False
    lead_time_days: int = Field(ge=1)
    inventory_buffer_days: int = Field(ge=0)
    criticality: Score = 0.5
    substitutable: bool = False
    attributes: dict[str, Any] = Field(default_factory=dict)


class SupplyChainBOMAssessment(BaseModel):
    """Evaluated vulnerability and resilience assessment for a Bill of Materials."""

    assessment_id: UUID = Field(default_factory=uuid4)
    system_or_product_name: str
    overall_supply_risk: Score
    critical_shortage_window_days: int
    single_source_choke_points: list[str]
    tier_1_risk: Score
    tier_2_risk: Score
    tier_3_risk: Score
    bottlenecks: list[str]
    resilience_recommendations: list[str]


class MultiTierSupplyEngine:
    """Evaluates multi-tier BOM risks and detects systemic supply vulnerabilities."""

    def assess_bom(
        self,
        system_name: str,
        components: list[BOMComponent],
        *,
        corridor_disruption_days: int = 0,
    ) -> SupplyChainBOMAssessment:
        if not components:
            raise ValueError("components list must not be empty")

        choke_points: list[str] = []
        bottlenecks: list[str] = []
        recommendations: list[str] = []

        tier_risks: dict[int, list[float]] = {1: [], 2: [], 3: []}
        min_buffer_days = 9999

        for comp in components:
            base_risk = comp.criticality * 0.4
            if comp.is_single_sourced:
                base_risk += 0.35
                choke_points.append(comp.component_id)
            if not comp.substitutable:
                base_risk += 0.15

            effective_buffer = comp.inventory_buffer_days - corridor_disruption_days
            if effective_buffer <= 0:
                base_risk += 0.20
                bottlenecks.append(
                    f"{comp.name} (Tier-{comp.tier}): Buffer exhausted ({effective_buffer}d margin)"
                )
            elif effective_buffer < comp.lead_time_days:
                base_risk += 0.10

            min_buffer_days = min(min_buffer_days, max(0, effective_buffer))
            tier_risks[comp.tier].append(min(1.0, base_risk))

        avg_tier_1 = sum(tier_risks[1]) / len(tier_risks[1]) if tier_risks[1] else 0.0
        avg_tier_2 = sum(tier_risks[2]) / len(tier_risks[2]) if tier_risks[2] else 0.0
        avg_tier_3 = sum(tier_risks[3]) / len(tier_risks[3]) if tier_risks[3] else 0.0

        # Weighted risk (Tier 1 direct impact + Tier 2 sub-assembly + Tier 3 raw materials)
        overall_risk = min(1.0, (avg_tier_1 * 0.50) + (avg_tier_2 * 0.30) + (avg_tier_3 * 0.20))

        if choke_points:
            recommendations.append(
                f"Establish dual-sourcing agreements for {len(choke_points)} single-sourced items"
            )
        if min_buffer_days < 14:
            recommendations.append(
                f"Increase inventory stockpile: critical shortage threshold in {min_buffer_days}d"
            )

        return SupplyChainBOMAssessment(
            system_or_product_name=system_name,
            overall_supply_risk=round(overall_risk, 4),
            critical_shortage_window_days=min_buffer_days,
            single_source_choke_points=choke_points,
            tier_1_risk=round(avg_tier_1, 4),
            tier_2_risk=round(avg_tier_2, 4),
            tier_3_risk=round(avg_tier_3, 4),
            bottlenecks=bottlenecks,
            resilience_recommendations=recommendations,
        )


class EconomicDisruptionEstimate(BaseModel):
    """Quantified financial and commercial loss projection from network disruption."""

    disruption_duration_days: int
    daily_holding_cost: float
    daily_demurrage_cost: float
    daily_production_loss_cost: float
    total_holding_cost: float
    total_demurrage_cost: float
    total_production_loss_cost: float
    total_estimated_loss_cad: float
    cost_breakdown_cad: dict[str, float]
    advisory_summary: str


class EconomicLossCalculator:
    """Calculates enterprise commercial losses from port demurrage, rail delays, and idling."""

    def calculate_losses(
        self,
        *,
        disruption_duration_days: int,
        daily_inventory_value_cad: float,
        vessels_delayed_count: int = 0,
        demurrage_rate_per_vessel_daily_cad: float = 25_000.0,
        production_line_daily_burn_cad: float = 150_000.0,
        holding_cost_annual_rate: float = 0.18,
    ) -> EconomicDisruptionEstimate:
        if disruption_duration_days < 0:
            raise ValueError("disruption_duration_days cannot be negative")

        daily_holding = (daily_inventory_value_cad * holding_cost_annual_rate) / 365.0
        daily_demurrage = float(vessels_delayed_count) * demurrage_rate_per_vessel_daily_cad
        daily_prod_loss = production_line_daily_burn_cad

        total_holding = daily_holding * disruption_duration_days
        total_demurrage = daily_demurrage * disruption_duration_days
        total_prod = daily_prod_loss * disruption_duration_days
        total_loss = total_holding + total_demurrage + total_prod

        breakdown = {
            "inventory_carrying_cost": round(total_holding, 2),
            "port_demurrage_and_detention": round(total_demurrage, 2),
            "production_line_stoppage": round(total_prod, 2),
        }

        summary = (
            f"Disruption duration: {disruption_duration_days} days. "
            f"Estimated total commercial loss: CAD ${total_loss:,.2f} "
            f"(Demurrage: ${total_demurrage:,.2f}, Production Loss: ${total_prod:,.2f})"
        )

        return EconomicDisruptionEstimate(
            disruption_duration_days=disruption_duration_days,
            daily_holding_cost=round(daily_holding, 2),
            daily_demurrage_cost=round(daily_demurrage, 2),
            daily_production_loss_cost=round(daily_prod_loss, 2),
            total_holding_cost=round(total_holding, 2),
            total_demurrage_cost=round(total_demurrage, 2),
            total_production_loss_cost=round(total_prod, 2),
            total_estimated_loss_cad=round(total_loss, 2),
            cost_breakdown_cad=breakdown,
            advisory_summary=summary,
        )


class ModalReroutingOption(BaseModel):
    """A feasible multi-modal rerouting corridor candidate."""

    mode: TransportMode
    origin: str
    destination: str
    transit_time_hours: float
    cost_per_ton_cad: float
    co2_kg_per_ton: float
    reliability_score: Score
    capacity_available: bool
    rationale: str


class ModalReroutingResult(BaseModel):
    """Ranked multi-modal rerouting options under corridor failure."""

    primary_corridor_disrupted: str
    recommended_mode: TransportMode
    total_options_evaluated: int
    ranked_options: list[ModalReroutingOption]
    tradeoff_analysis: str


class ModalReroutingSolver:
    """Solves deterministic multi-modal freight rerouting under corridor blockages."""

    DEFAULT_MODAL_BASELINES: ClassVar[dict[TransportMode, dict[str, float]]] = {
        TransportMode.MARITIME: {
            "speed_kmh": 25.0,
            "cost_per_ton_km": 0.04,
            "co2_kg_ton_km": 0.015,
            "base_reliability": 0.88,
        },
        TransportMode.RAIL_CPKC: {
            "speed_kmh": 45.0,
            "cost_per_ton_km": 0.08,
            "co2_kg_ton_km": 0.025,
            "base_reliability": 0.92,
        },
        TransportMode.RAIL_CN: {
            "speed_kmh": 45.0,
            "cost_per_ton_km": 0.08,
            "co2_kg_ton_km": 0.025,
            "base_reliability": 0.92,
        },
        TransportMode.LONG_HAUL_TRUCK: {
            "speed_kmh": 85.0,
            "cost_per_ton_km": 0.28,
            "co2_kg_ton_km": 0.110,
            "base_reliability": 0.95,
        },
        TransportMode.AIR_CARGO: {
            "speed_kmh": 650.0,
            "cost_per_ton_km": 1.45,
            "co2_kg_ton_km": 0.650,
            "base_reliability": 0.98,
        },
    }

    def solve_rerouting(
        self,
        *,
        corridor_id: str,
        origin: str,
        destination: str,
        distance_km: float,
        time_critical: bool = False,
        budget_constrained: bool = False,
    ) -> ModalReroutingResult:
        options: list[ModalReroutingOption] = []

        for mode, params in self.DEFAULT_MODAL_BASELINES.items():
            transit_hours = distance_km / params["speed_kmh"]
            cost_ton = distance_km * params["cost_per_ton_km"]
            co2_ton = distance_km * params["co2_kg_ton_km"]
            reliability = float(params["base_reliability"])

            rationale = (
                f"{mode.value.upper()}: Transit {transit_hours:.1f}h, "
                f"CAD ${cost_ton:.2f}/ton, {co2_ton:.1f}kg CO2/ton"
            )

            options.append(
                ModalReroutingOption(
                    mode=mode,
                    origin=origin,
                    destination=destination,
                    transit_time_hours=round(transit_hours, 1),
                    cost_per_ton_cad=round(cost_ton, 2),
                    co2_kg_per_ton=round(co2_ton, 2),
                    reliability_score=reliability,
                    capacity_available=True,
                    rationale=rationale,
                )
            )

        if time_critical:
            options.sort(key=lambda opt: opt.transit_time_hours)
            tradeoff = "Prioritized fastest delivery transit speed due to time-criticality."
        elif budget_constrained:
            options.sort(key=lambda opt: opt.cost_per_ton_cad)
            tradeoff = "Prioritized lowest freight cost under budget constraint."
        else:
            options.sort(
                key=lambda opt: (
                    (opt.cost_per_ton_cad * 0.5 + opt.transit_time_hours * 0.5)
                    / opt.reliability_score
                )
            )
            tradeoff = "Balanced optimization between cost, transit velocity, and reliability."

        recommended = options[0].mode

        return ModalReroutingResult(
            primary_corridor_disrupted=corridor_id,
            recommended_mode=recommended,
            total_options_evaluated=len(options),
            ranked_options=options,
            tradeoff_analysis=tradeoff,
        )
