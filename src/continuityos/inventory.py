"""Inventory depletion engine.

Models strategic inventories over time with deterministic day-by-day simulation.
Calculates days-to-warning, days-to-critical, and days-to-exhaustion under
normal, degraded, and disrupted replenishment conditions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from continuityos.domain import Score


class InventoryProfile(BaseModel):
    """Configuration for a strategic inventory resource."""

    resource_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    starting_quantity: float = Field(gt=0)
    unit: str = Field(default="liters", min_length=1, max_length=32)
    normal_consumption_per_day: float = Field(gt=0)
    degraded_consumption_per_day: float | None = None
    replenishment_per_day: float = Field(default=0.0, ge=0)
    replenishment_delay_days: int = Field(default=0, ge=0, le=365)
    route_capacity_factor: Score = 1.0
    substitution_factor: Score = 0.0
    minimum_reserve: float = Field(ge=0)
    critical_threshold: float = Field(ge=0)
    warning_threshold: float | None = None


class InventoryDay(BaseModel):
    """State of an inventory resource on a single day."""

    day: int
    quantity: float
    consumption: float
    replenishment: float
    status: str  # "normal", "warning", "critical", "exhausted"


class InventoryResult(BaseModel):
    """Result of inventory depletion simulation."""

    resource_id: str
    name: str
    starting_quantity: float
    unit: str
    days_to_warning: int | None = None
    days_to_critical: int | None = None
    days_to_exhaustion: int | None = None
    final_quantity: float
    final_status: str
    daily_log: list[InventoryDay]
    summary: str


def simulate_inventory(
    profile: InventoryProfile,
    simulation_days: int = 90,
    *,
    degraded: bool = False,
    disrupted_replenishment: bool = False,
) -> InventoryResult:
    """Simulate inventory depletion over time.

    Args:
        profile: Inventory configuration.
        simulation_days: Number of days to simulate.
        degraded: If True, use degraded consumption rate.
        disrupted_replenishment: If True, disable replenishment entirely.
    """
    quantity = profile.starting_quantity
    consumption_rate = (
        profile.degraded_consumption_per_day
        if degraded and profile.degraded_consumption_per_day is not None
        else profile.normal_consumption_per_day
    )

    warning_threshold = (
        profile.warning_threshold
        if profile.warning_threshold is not None
        else profile.minimum_reserve * 1.5
    )

    days_to_warning: int | None = None
    days_to_critical: int | None = None
    days_to_exhaustion: int | None = None
    daily_log: list[InventoryDay] = []

    for day in range(simulation_days):
        # Determine replenishment
        replenishment = 0.0
        if (
            not disrupted_replenishment
            and day >= profile.replenishment_delay_days
            and profile.replenishment_per_day > 0
        ):
            replenishment = (
                profile.replenishment_per_day
                * profile.route_capacity_factor
            )

        # Apply substitution (reduces effective consumption)
        effective_consumption = consumption_rate * (1.0 - profile.substitution_factor)

        # Update quantity
        quantity = quantity - effective_consumption + replenishment
        quantity = max(0.0, quantity)

        # Determine status
        if quantity <= 0:
            status = "exhausted"
        elif quantity <= profile.critical_threshold:
            status = "critical"
        elif quantity <= warning_threshold:
            status = "warning"
        else:
            status = "normal"

        daily_log.append(InventoryDay(
            day=day,
            quantity=round(quantity, 2),
            consumption=round(effective_consumption, 2),
            replenishment=round(replenishment, 2),
            status=status,
        ))

        # Track threshold crossings (first occurrence only)
        if days_to_warning is None and quantity <= warning_threshold:
            days_to_warning = day
        if days_to_critical is None and quantity <= profile.critical_threshold:
            days_to_critical = day
        if days_to_exhaustion is None and quantity <= 0:
            days_to_exhaustion = day

    final = daily_log[-1] if daily_log else InventoryDay(
        day=0, quantity=quantity, consumption=0, replenishment=0, status="normal"
    )

    # Build summary
    parts = [
        f"{profile.name}: {profile.starting_quantity:,.0f} {profile.unit}",
        f"consumption: {consumption_rate:,.0f}/{profile.unit}/day",
    ]
    if days_to_warning is not None:
        parts.append(f"warning at day {days_to_warning}")
    if days_to_critical is not None:
        parts.append(f"critical at day {days_to_critical}")
    if days_to_exhaustion is not None:
        parts.append(f"exhausted at day {days_to_exhaustion}")
    else:
        parts.append(f"remaining after {simulation_days} days: {final.quantity:,.0f}")

    return InventoryResult(
        resource_id=profile.resource_id,
        name=profile.name,
        starting_quantity=profile.starting_quantity,
        unit=profile.unit,
        days_to_warning=days_to_warning,
        days_to_critical=days_to_critical,
        days_to_exhaustion=days_to_exhaustion,
        final_quantity=round(final.quantity, 2),
        final_status=final.status,
        daily_log=daily_log,
        summary="; ".join(parts),
    )
