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
    emergency_consumption_per_day: float | None = None
    replenishment_per_day: float = Field(default=0.0, ge=0)
    replenishment_delay_days: int = Field(default=0, ge=0, le=365)
    shipment_delay_days: int = Field(default=0, ge=0, le=365)
    route_capacity_factor: Score = 1.0
    substitution_factor: Score = 0.0
    minimum_reserve: float = Field(ge=0)
    critical_threshold: float = Field(ge=0)
    warning_threshold: float | None = None
    storage_capacity_limit: float | None = None
    alternate_supplier_daily_rate: float = Field(default=0.0, ge=0)
    alternate_supplier_delay_days: int = Field(default=0, ge=0, le=365)


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
    days_to_replenishment: int | None = None
    minimum_inventory_during_event: float = 0.0
    time_to_restore_reserve: int | None = None
    assured_replenishment_days: int = 0
    final_quantity: float
    final_status: str
    daily_log: list[InventoryDay]
    summary: str


def simulate_inventory(
    profile: InventoryProfile,
    simulation_days: int = 90,
    *,
    degraded: bool = False,
    emergency: bool = False,
    disrupted_replenishment: bool = False,
) -> InventoryResult:
    """Simulate strategic inventory depletion and replenishment over time.

    Args:
        profile: Strategic inventory configuration.
        simulation_days: Number of days to simulate.
        degraded: If True, use degraded consumption rate.
        emergency: If True, use emergency burn rate.
        disrupted_replenishment: If True, disable primary replenishment.
    """
    quantity = profile.starting_quantity
    if emergency and profile.emergency_consumption_per_day is not None:
        consumption_rate = profile.emergency_consumption_per_day
    elif degraded and profile.degraded_consumption_per_day is not None:
        consumption_rate = profile.degraded_consumption_per_day
    else:
        consumption_rate = profile.normal_consumption_per_day

    warning_threshold = (
        profile.warning_threshold
        if profile.warning_threshold is not None
        else profile.minimum_reserve * 1.5
    )

    days_to_warning: int | None = None
    days_to_critical: int | None = None
    days_to_exhaustion: int | None = None
    days_to_replenishment: int | None = None
    min_inventory = quantity
    time_to_restore_reserve: int | None = None
    dropped_below_reserve = quantity < profile.minimum_reserve

    daily_log: list[InventoryDay] = []

    # Calculate assured replenishment days KPI:
    # When is the first credible replenishment actually expected to arrive?
    if not disrupted_replenishment and profile.replenishment_per_day > 0:
        assured_replenishment_days = profile.replenishment_delay_days + profile.shipment_delay_days
    elif profile.alternate_supplier_daily_rate > 0:
        assured_replenishment_days = profile.alternate_supplier_delay_days
    else:
        assured_replenishment_days = simulation_days

    effective_replenishment_start = profile.replenishment_delay_days + profile.shipment_delay_days

    for day in range(simulation_days):
        # Determine replenishment
        replenishment = 0.0
        if (
            not disrupted_replenishment
            and day >= effective_replenishment_start
            and profile.replenishment_per_day > 0
        ):
            replenishment += profile.replenishment_per_day * profile.route_capacity_factor

        # Alternate supplier activation if primary disrupted
        if (
            disrupted_replenishment
            and profile.alternate_supplier_daily_rate > 0
            and day >= profile.alternate_supplier_delay_days
        ):
            replenishment += profile.alternate_supplier_daily_rate

        if replenishment > 0 and days_to_replenishment is None:
            days_to_replenishment = day

        # Apply substitution (reduces effective consumption)
        effective_consumption = consumption_rate * (1.0 - profile.substitution_factor)

        # Update quantity
        quantity = quantity - effective_consumption + replenishment
        if profile.storage_capacity_limit is not None:
            quantity = min(quantity, profile.storage_capacity_limit)
        quantity = max(0.0, quantity)

        if quantity < min_inventory:
            min_inventory = quantity

        if quantity < profile.minimum_reserve:
            dropped_below_reserve = True
        elif (
            dropped_below_reserve
            and quantity >= profile.minimum_reserve
            and time_to_restore_reserve is None
        ):
            time_to_restore_reserve = day

        # Determine status
        if quantity <= 0:
            status = "exhausted"
        elif quantity <= profile.critical_threshold:
            status = "critical"
        elif quantity <= warning_threshold:
            status = "warning"
        else:
            status = "normal"

        daily_log.append(
            InventoryDay(
                day=day,
                quantity=round(quantity, 2),
                consumption=round(effective_consumption, 2),
                replenishment=round(replenishment, 2),
                status=status,
            )
        )

        # Track threshold crossings (first occurrence only)
        if days_to_warning is None and quantity <= warning_threshold:
            days_to_warning = day
        if days_to_critical is None and quantity <= profile.critical_threshold:
            days_to_critical = day
        if days_to_exhaustion is None and quantity <= 0:
            days_to_exhaustion = day

    final = (
        daily_log[-1]
        if daily_log
        else InventoryDay(day=0, quantity=quantity, consumption=0, replenishment=0, status="normal")
    )

    # Build summary
    parts = [
        f"{profile.name}: {profile.starting_quantity:,.0f} {profile.unit}",
        f"consumption: {consumption_rate:,.0f}/{profile.unit}/day",
        f"assured replenishment: {assured_replenishment_days} days",
    ]
    if days_to_warning is not None:
        parts.append(f"warning at day {days_to_warning}")
    if days_to_critical is not None:
        parts.append(f"critical at day {days_to_critical}")
    if days_to_exhaustion is not None:
        parts.append(f"exhausted at day {days_to_exhaustion}")
    else:
        parts.append(f"remaining after {simulation_days} days: {final.quantity:,.0f}")
    if time_to_restore_reserve is not None:
        parts.append(f"reserve restored at day {time_to_restore_reserve}")

    return InventoryResult(
        resource_id=profile.resource_id,
        name=profile.name,
        starting_quantity=profile.starting_quantity,
        unit=profile.unit,
        days_to_warning=days_to_warning,
        days_to_critical=days_to_critical,
        days_to_exhaustion=days_to_exhaustion,
        days_to_replenishment=days_to_replenishment,
        minimum_inventory_during_event=round(min_inventory, 2),
        time_to_restore_reserve=time_to_restore_reserve,
        assured_replenishment_days=assured_replenishment_days,
        final_quantity=round(final.quantity, 2),
        final_status=final.status,
        daily_log=daily_log,
        summary="; ".join(parts),
    )
