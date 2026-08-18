"""Policy-as-Code engine for ContinuityOS.

Evaluates organizational continuity policies against observed supply network
state. Policies are declarative, versionable, testable, and auditable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.domain import Score


class PolicyAssertion(BaseModel):
    """A single assertion within a policy rule."""

    minimum_providers: int | None = None
    minimum_reserve_days: int | None = None
    minimum_independent_routes: int | None = None
    minimum_continuity: float | None = None
    maximum_single_dependency_concentration: float | None = None
    minimum_trust_score: float | None = None


class PolicyRule(BaseModel):
    """A named, testable policy rule with an assertion."""

    rule_id: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=512)
    assertion: PolicyAssertion
    severity: str = Field(default="error", pattern=r"^(error|warning|info)$")


class ContinuityPolicy(BaseModel):
    """A set of continuity rules to evaluate against observed state."""

    policy_id: str = Field(default="default", min_length=1, max_length=128)
    version: str = Field(default="1.0", min_length=1, max_length=32)
    rules: list[PolicyRule] = Field(min_length=1, max_length=500)


class ObservedState(BaseModel):
    """Observed supply network state to evaluate against a policy."""

    provider_counts: dict[str, int] = Field(default_factory=dict)
    reserve_days: dict[str, float] = Field(default_factory=dict)
    independent_route_count: int = Field(default=0, ge=0)
    overall_continuity: Score = 0.0
    dependency_concentration: dict[str, float] = Field(default_factory=dict)
    trust_scores: dict[str, float] = Field(default_factory=dict)


class PolicyViolation(BaseModel):
    """A single policy violation with expected vs. observed state."""

    rule_id: str
    description: str
    severity: str
    expected: str
    observed: str
    deficit: str | None = None


class PolicyEvaluation(BaseModel):
    """Result of evaluating a policy against observed state."""

    evaluation_id: UUID = Field(default_factory=uuid4)
    policy_id: str
    policy_version: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    compliant: bool
    violations: list[PolicyViolation]
    rules_evaluated: int
    rules_passed: int


def evaluate_policy(policy: ContinuityPolicy, state: ObservedState) -> PolicyEvaluation:
    """Evaluate a ContinuityPolicy against an ObservedState."""
    violations: list[PolicyViolation] = []
    rules_passed = 0

    for rule in policy.rules:
        violation = _check_rule(rule, state)
        if violation:
            violations.append(violation)
        else:
            rules_passed += 1

    return PolicyEvaluation(
        policy_id=policy.policy_id,
        policy_version=policy.version,
        compliant=len(violations) == 0,
        violations=violations,
        rules_evaluated=len(policy.rules),
        rules_passed=rules_passed,
    )


def _check_rule(rule: PolicyRule, state: ObservedState) -> PolicyViolation | None:
    """Check a single rule, returning a violation if it fails."""
    assertion = rule.assertion

    if assertion.minimum_providers is not None:
        for category, count in state.provider_counts.items():
            if count < assertion.minimum_providers:
                return PolicyViolation(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    severity=rule.severity,
                    expected=f">= {assertion.minimum_providers} providers ({category})",
                    observed=f"{count} providers",
                    deficit=f"{assertion.minimum_providers - count} additional required",
                )

    if assertion.minimum_reserve_days is not None:
        for resource, days in state.reserve_days.items():
            if days < assertion.minimum_reserve_days:
                return PolicyViolation(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    severity=rule.severity,
                    expected=f">= {assertion.minimum_reserve_days} days ({resource})",
                    observed=f"{days:.1f} days",
                    deficit=f"{assertion.minimum_reserve_days - days:.1f} days short",
                )

    if assertion.minimum_independent_routes is not None:
        if state.independent_route_count < assertion.minimum_independent_routes:
            return PolicyViolation(
                rule_id=rule.rule_id,
                description=rule.description,
                severity=rule.severity,
                expected=f">= {assertion.minimum_independent_routes} independent routes",
                observed=f"{state.independent_route_count} routes",
                deficit=f"{assertion.minimum_independent_routes - state.independent_route_count} additional required",
            )

    if assertion.minimum_continuity is not None:
        if state.overall_continuity < assertion.minimum_continuity:
            return PolicyViolation(
                rule_id=rule.rule_id,
                description=rule.description,
                severity=rule.severity,
                expected=f">= {assertion.minimum_continuity:.1%} continuity",
                observed=f"{state.overall_continuity:.1%}",
                deficit=f"{assertion.minimum_continuity - state.overall_continuity:.1%} below target",
            )

    if assertion.minimum_trust_score is not None:
        for dep, score in state.trust_scores.items():
            if score < assertion.minimum_trust_score:
                return PolicyViolation(
                    rule_id=rule.rule_id,
                    description=rule.description,
                    severity=rule.severity,
                    expected=f">= {assertion.minimum_trust_score:.2f} trust ({dep})",
                    observed=f"{score:.2f}",
                    deficit=f"{assertion.minimum_trust_score - score:.2f} below threshold",
                )

    return None
