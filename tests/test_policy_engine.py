"""Tests for Policy-as-Code declarative evaluation engine."""

from __future__ import annotations

from continuityos.policy import (
    ContinuityPolicy,
    ObservedState,
    PolicyAssertion,
    PolicyRule,
    evaluate_policy,
)


class TestPolicyEngine:
    def test_all_rules_pass(self) -> None:
        policy = ContinuityPolicy(
            policy_id="test-pol",
            version="1.0",
            rules=[
                PolicyRule(
                    rule_id="SAT-001",
                    description="SATCOM redundancy",
                    assertion=PolicyAssertion(minimum_providers=2),
                ),
                PolicyRule(
                    rule_id="INV-001",
                    description="Fuel reserve days",
                    assertion=PolicyAssertion(minimum_reserve_days=30),
                ),
                PolicyRule(
                    rule_id="RTE-001",
                    description="Independent routes",
                    assertion=PolicyAssertion(minimum_independent_routes=2),
                ),
                PolicyRule(
                    rule_id="CONT-001",
                    description="Minimum continuity",
                    assertion=PolicyAssertion(minimum_continuity=0.90),
                ),
                PolicyRule(
                    rule_id="TRST-001",
                    description="Minimum trust",
                    assertion=PolicyAssertion(minimum_trust_score=0.70),
                ),
            ],
        )
        state = ObservedState(
            provider_counts={"satcom": 3, "icebreaker": 2},
            reserve_days={"fuel": 45.0, "medical": 60.0},
            independent_route_count=3,
            overall_continuity=0.96,
            trust_scores={"satcom": 0.85, "navigation": 0.90},
        )
        evaluation = evaluate_policy(policy, state)
        assert evaluation.compliant is True
        assert evaluation.rules_evaluated == 5
        assert evaluation.rules_passed == 5
        assert len(evaluation.violations) == 0

    def test_policy_violations_detected_with_deficits(self) -> None:
        policy = ContinuityPolicy(
            policy_id="strict-arctic",
            version="2.0",
            rules=[
                PolicyRule(
                    rule_id="SAT-001",
                    description="SATCOM redundancy",
                    assertion=PolicyAssertion(minimum_providers=2),
                ),
                PolicyRule(
                    rule_id="INV-001",
                    description="Fuel reserve days",
                    assertion=PolicyAssertion(minimum_reserve_days=30),
                ),
                PolicyRule(
                    rule_id="RTE-001",
                    description="Independent routes",
                    assertion=PolicyAssertion(minimum_independent_routes=3),
                ),
            ],
        )
        state = ObservedState(
            provider_counts={"satcom": 1},  # Violated (1 < 2)
            reserve_days={"fuel": 20.0},     # Violated (20 < 30)
            independent_route_count=2,       # Violated (2 < 3)
            overall_continuity=0.75,
        )
        evaluation = evaluate_policy(policy, state)
        assert evaluation.compliant is False
        assert len(evaluation.violations) == 3
        assert evaluation.rules_passed == 0

        v_sat = next(v for v in evaluation.violations if v.rule_id == "SAT-001")
        assert "1 providers" in v_sat.observed
        assert "1 additional required" in (v_sat.deficit or "")

        v_inv = next(v for v in evaluation.violations if v.rule_id == "INV-001")
        assert "20.0 days" in v_inv.observed
        assert "10.0 days short" in (v_inv.deficit or "")
