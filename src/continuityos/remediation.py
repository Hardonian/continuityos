"""Remediation engine.

Generates defensive continuity options. All remediation is ADVISORY —
never auto-executed. Each option includes estimated continuity improvement,
cost, dependency changes, constraints, and confidence.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score
from continuityos.reconcile import ReconciliationCheck, ReconciliationResult, ReconciliationStatus


class RemediationOption(BaseModel):
    """A single advisory remediation option."""

    option_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=1024)
    addresses_check: str
    estimated_continuity_improvement: Score
    estimated_cost: float | None = None
    dependency_changes: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    confidence: Score = 0.5
    requires_human_approval: bool = True
    priority: int = Field(default=1, ge=1, le=5)


class RemediationPlan(BaseModel):
    """A set of advisory remediation options."""

    plan_id: UUID = Field(default_factory=uuid4)
    options: list[RemediationOption]
    total_estimated_improvement: Score
    advisory_notice: str = (
        "All remediation options are advisory. Human review and approval "
        "is required before any action is taken. ContinuityOS does not "
        "automatically execute remediation actions."
    )
    summary: str


# Remediation templates for common violations
_REMEDIATION_TEMPLATES: dict[str, list[dict[str, object]]] = {
    "SATCOM_PROVIDER_COUNT": [
        {
            "name": "Add second SATCOM provider",
            "description": "Contract an independent satellite communications provider to eliminate single-provider dependency",
            "improvement": 0.15,
            "priority": 1,
        },
        {
            "name": "Deploy backup HF radio",
            "description": "Install HF radio as independent communications fallback",
            "improvement": 0.08,
            "priority": 2,
        },
    ],
    "FUEL_RESERVE": [
        {
            "name": "Emergency fuel resupply",
            "description": "Schedule priority fuel delivery via available route",
            "improvement": 0.12,
            "priority": 1,
        },
        {
            "name": "Reduce non-essential fuel consumption",
            "description": "Implement fuel conservation measures to extend reserves",
            "improvement": 0.06,
            "priority": 2,
        },
    ],
    "MEDICAL_RESERVE": [
        {
            "name": "Emergency medical resupply",
            "description": "Schedule priority medical supply delivery",
            "improvement": 0.10,
            "priority": 1,
        },
    ],
    "ROUTE_COUNT": [
        {
            "name": "Activate alternate route",
            "description": "Open secondary supply route through alternate corridor",
            "improvement": 0.15,
            "priority": 1,
        },
        {
            "name": "Pre-position critical supplies",
            "description": "Forward-deploy critical inventory to reduce route dependency",
            "improvement": 0.08,
            "priority": 2,
        },
    ],
    "NAVIGATION_SOURCE_COUNT": [
        {
            "name": "Add independent navigation source",
            "description": "Deploy additional GNSS/PNT receiver or inertial navigation backup",
            "improvement": 0.10,
            "priority": 1,
        },
    ],
    "OVERALL_CONTINUITY": [
        {
            "name": "Reduce dependency concentration",
            "description": "Diversify critical service providers across independent vendors",
            "improvement": 0.10,
            "priority": 1,
        },
        {
            "name": "Increase reserve inventory",
            "description": "Build additional strategic reserves for critical commodities",
            "improvement": 0.08,
            "priority": 2,
        },
        {
            "name": "Add second communications provider",
            "description": "Contract independent backup communications service",
            "improvement": 0.12,
            "priority": 1,
        },
    ],
}


def generate_remediation(
    reconciliation: ReconciliationResult,
) -> RemediationPlan:
    """Generate advisory remediation options from reconciliation results.

    All options are advisory. Never auto-executes.
    """
    options: list[RemediationOption] = []

    for check in reconciliation.checks:
        if check.status in {ReconciliationStatus.COMPLIANT}:
            continue

        check_options = _generate_options_for_check(check)
        options.extend(check_options)

    # Sort by priority then estimated improvement
    options.sort(key=lambda o: (o.priority, -o.estimated_continuity_improvement))

    total_improvement = min(
        1.0,
        sum(o.estimated_continuity_improvement for o in options),
    )

    summary_parts = [f"{len(options)} remediation options generated"]
    if options:
        summary_parts.append(
            f"estimated total improvement: {total_improvement:.1%}"
        )
    failed = [c for c in reconciliation.checks if c.status == ReconciliationStatus.FAIL]
    if failed:
        summary_parts.append(f"{len(failed)} critical failures addressed")

    return RemediationPlan(
        options=options,
        total_estimated_improvement=round(total_improvement, 6),
        summary="; ".join(summary_parts),
    )


def _generate_options_for_check(check: ReconciliationCheck) -> list[RemediationOption]:
    """Generate remediation options for a specific failing check."""
    templates = _REMEDIATION_TEMPLATES.get(check.check_id, [])

    if not templates:
        # Generate a generic option for unknown check types
        return [RemediationOption(
            name=f"Address {check.check_id}",
            description=f"Remediate: {check.description}. {check.deficit or ''}".strip(),
            addresses_check=check.check_id,
            estimated_continuity_improvement=0.05,
            confidence=0.3,
            priority=3,
        )]

    options: list[RemediationOption] = []
    for template in templates:
        options.append(RemediationOption(
            name=str(template["name"]),
            description=str(template["description"]),
            addresses_check=check.check_id,
            estimated_continuity_improvement=float(template.get("improvement", 0.05)),
            confidence=0.5,
            priority=int(template.get("priority", 2)),
        ))
    return options
