"""Kubernetes/Terraform-style desired-vs-observed state reconciliation.

Compares the declared resilience state (ContinuityPolicy) against observed
real-world state and produces a deterministic reconciliation status with
per-check details.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class ReconciliationStatus(StrEnum):
    COMPLIANT = "compliant"
    DRIFT = "drift"
    DEGRADED = "degraded"
    FAIL = "fail"
    UNKNOWN = "unknown"


class ReconciliationCheck(BaseModel):
    """A single reconciliation check result."""

    check_id: str
    description: str
    desired: str
    observed: str
    status: ReconciliationStatus
    deficit: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ReconciliationResult(BaseModel):
    """Complete reconciliation output."""

    reconciliation_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_status: ReconciliationStatus
    checks: list[ReconciliationCheck]
    compliant_count: int
    drift_count: int
    degraded_count: int
    fail_count: int
    unknown_count: int
    summary: str


class DesiredState(BaseModel):
    """Declared resilience requirements."""

    satcom_provider_count: int | None = None
    fuel_reserve_days: float | None = None
    medical_reserve_days: float | None = None
    minimum_routes: int | None = None
    minimum_continuity: Score | None = None
    navigation_source_count: int | None = None
    observation_source_count: int | None = None
    minimum_trust_score: Score | None = None
    custom_checks: dict[str, float] = Field(default_factory=dict)


class ActualState(BaseModel):
    """Observed real-world state."""

    satcom_provider_count: int | None = None
    fuel_reserve_days: float | None = None
    medical_reserve_days: float | None = None
    route_count: int | None = None
    overall_continuity: Score | None = None
    navigation_source_count: int | None = None
    observation_source_count: int | None = None
    trust_scores: dict[str, float] = Field(default_factory=dict)
    custom_values: dict[str, float] = Field(default_factory=dict)


def reconcile(desired: DesiredState, actual: ActualState) -> ReconciliationResult:
    """Reconcile desired vs. observed state and produce a status report."""
    checks: list[ReconciliationCheck] = []

    if desired.satcom_provider_count is not None:
        checks.append(
            _compare_int(
                "SATCOM_PROVIDER_COUNT",
                "SATCOM providers must meet redundancy requirement",
                desired.satcom_provider_count,
                actual.satcom_provider_count,
            )
        )

    if desired.fuel_reserve_days is not None:
        checks.append(
            _compare_float(
                "FUEL_RESERVE",
                "Fuel reserve must meet minimum days",
                desired.fuel_reserve_days,
                actual.fuel_reserve_days,
                unit="days",
            )
        )

    if desired.medical_reserve_days is not None:
        checks.append(
            _compare_float(
                "MEDICAL_RESERVE",
                "Medical reserve must meet minimum days",
                desired.medical_reserve_days,
                actual.medical_reserve_days,
                unit="days",
            )
        )

    if desired.minimum_routes is not None:
        checks.append(
            _compare_int(
                "ROUTE_COUNT",
                "Independent routes must meet minimum",
                desired.minimum_routes,
                actual.route_count,
            )
        )

    if desired.minimum_continuity is not None:
        checks.append(
            _compare_float(
                "OVERALL_CONTINUITY",
                "Overall continuity must meet target",
                desired.minimum_continuity,
                actual.overall_continuity,
                unit="ratio",
            )
        )

    if desired.navigation_source_count is not None:
        checks.append(
            _compare_int(
                "NAVIGATION_SOURCE_COUNT",
                "Navigation sources must meet minimum",
                desired.navigation_source_count,
                actual.navigation_source_count,
            )
        )

    if desired.observation_source_count is not None:
        checks.append(
            _compare_int(
                "OBSERVATION_SOURCE_COUNT",
                "Observation sources must meet minimum",
                desired.observation_source_count,
                actual.observation_source_count,
            )
        )

    for key, desired_value in desired.custom_checks.items():
        observed_value = actual.custom_values.get(key)
        checks.append(
            _compare_float(
                key,
                f"Custom check: {key}",
                desired_value,
                observed_value,
                unit="",
            )
        )

    # Determine overall status
    statuses = [check.status for check in checks]
    compliant = statuses.count(ReconciliationStatus.COMPLIANT)
    drift = statuses.count(ReconciliationStatus.DRIFT)
    degraded = statuses.count(ReconciliationStatus.DEGRADED)
    fail = statuses.count(ReconciliationStatus.FAIL)
    unknown = statuses.count(ReconciliationStatus.UNKNOWN)

    if fail > 0:
        overall = ReconciliationStatus.FAIL
    elif degraded > 0:
        overall = ReconciliationStatus.DEGRADED
    elif drift > 0:
        overall = ReconciliationStatus.DRIFT
    elif unknown > 0:
        overall = ReconciliationStatus.UNKNOWN
    else:
        overall = ReconciliationStatus.COMPLIANT

    summary = (
        f"{len(checks)} checks: {compliant} compliant, {drift} drift, "
        f"{degraded} degraded, {fail} fail, {unknown} unknown"
    )

    return ReconciliationResult(
        overall_status=overall,
        checks=checks,
        compliant_count=compliant,
        drift_count=drift,
        degraded_count=degraded,
        fail_count=fail,
        unknown_count=unknown,
        summary=summary,
    )


def _compare_int(
    check_id: str,
    description: str,
    desired: int,
    observed: int | None,
) -> ReconciliationCheck:
    if observed is None:
        return ReconciliationCheck(
            check_id=check_id,
            description=description,
            desired=f">= {desired}",
            observed="unknown",
            status=ReconciliationStatus.UNKNOWN,
        )
    if observed >= desired:
        return ReconciliationCheck(
            check_id=check_id,
            description=description,
            desired=f">= {desired}",
            observed=str(observed),
            status=ReconciliationStatus.COMPLIANT,
        )
    ratio = observed / desired if desired > 0 else 0.0
    if ratio >= 0.8:
        status = ReconciliationStatus.DRIFT
    elif ratio >= 0.5:
        status = ReconciliationStatus.DEGRADED
    else:
        status = ReconciliationStatus.FAIL
    return ReconciliationCheck(
        check_id=check_id,
        description=description,
        desired=f">= {desired}",
        observed=str(observed),
        status=status,
        deficit=f"{desired - observed} below target",
    )


def _compare_float(
    check_id: str,
    description: str,
    desired: float,
    observed: float | None,
    *,
    unit: str = "",
) -> ReconciliationCheck:
    if observed is None:
        return ReconciliationCheck(
            check_id=check_id,
            description=description,
            desired=f">= {desired} {unit}".strip(),
            observed="unknown",
            status=ReconciliationStatus.UNKNOWN,
        )
    if observed >= desired:
        return ReconciliationCheck(
            check_id=check_id,
            description=description,
            desired=f">= {desired} {unit}".strip(),
            observed=f"{observed} {unit}".strip(),
            status=ReconciliationStatus.COMPLIANT,
        )
    ratio = observed / desired if desired > 0 else 0.0
    if ratio >= 0.8:
        status = ReconciliationStatus.DRIFT
    elif ratio >= 0.5:
        status = ReconciliationStatus.DEGRADED
    else:
        status = ReconciliationStatus.FAIL
    return ReconciliationCheck(
        check_id=check_id,
        description=description,
        desired=f">= {desired} {unit}".strip(),
        observed=f"{observed} {unit}".strip(),
        status=status,
        deficit=f"{desired - observed:.1f} {unit} below target".strip(),
    )
