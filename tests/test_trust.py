"""Tests for DependencyTrust engine and multi-dimensional trust evaluation."""

from __future__ import annotations

import pytest

from continuityos.trust import (
    DependencyTrust,
    TrustAggregation,
    TrustDimensions,
    TrustProvenance,
    evaluate_trust,
)


class TestDependencyTrust:
    def test_default_trust_dimensions(self) -> None:
        dims = TrustDimensions()
        assert len(dims.all_values()) == 9
        assert all(v == 1.0 for v in dims.all_values())
        assert len(dims.dimension_names()) == 9
        assert dims.as_dict()["physical_availability"] == 1.0

    def test_aggregation_minimum(self) -> None:
        trust = DependencyTrust(
            dependency_ref="satcom/iridium",
            dimensions=TrustDimensions(
                physical_availability=0.9,
                cyber_integrity=0.6,
                navigation_integrity=0.95,
            ),
            aggregation=TrustAggregation.MINIMUM,
        )
        assert trust.aggregate_score() == 0.6
        name, val = trust.weakest_dimension()
        assert name == "cyber_integrity"
        assert val == 0.6

    def test_aggregation_mean(self) -> None:
        trust = DependencyTrust(
            dependency_ref="port/kirkenes",
            dimensions=TrustDimensions(
                physical_availability=0.8,
                cyber_integrity=0.8,
                legal_availability=0.8,
                commercial_availability=0.8,
                insurance_availability=0.8,
                communications_integrity=0.8,
                navigation_integrity=0.8,
                operator_confidence=0.8,
                information_confidence=0.8,
            ),
            aggregation=TrustAggregation.MEAN,
        )
        assert pytest.approx(trust.aggregate_score(), 0.01) == 0.8

    def test_aggregation_weighted(self) -> None:
        trust = DependencyTrust(
            dependency_ref="route/nsr",
            dimensions=TrustDimensions(
                physical_availability=0.5,
                cyber_integrity=0.5,
                legal_availability=1.0,
                commercial_availability=1.0,
                insurance_availability=1.0,
                communications_integrity=1.0,
                navigation_integrity=1.0,
                operator_confidence=1.0,
                information_confidence=1.0,
            ),
            aggregation=TrustAggregation.WEIGHTED,
        )
        score = trust.aggregate_score()
        assert 0.5 < score < 1.0

    def test_provenance_requirement(self) -> None:
        trust_unmet = DependencyTrust(
            dependency_ref="ice/service",
            dimensions=TrustDimensions(physical_availability=0.9),
            provenance=TrustProvenance(minimum_independent_sources=3, actual_independent_sources=1),
        )
        assert not trust_unmet.provenance_met()
        assessment = evaluate_trust(trust_unmet)
        assert not assessment.provenance_met
        assert any("insufficient independent sources" in r for r in assessment.reason_codes)

        trust_met = DependencyTrust(
            dependency_ref="ice/service",
            dimensions=TrustDimensions(physical_availability=0.9),
            provenance=TrustProvenance(
                minimum_independent_sources=2,
                actual_independent_sources=2,
                source_ids=["noaa", "copernicus"],
            ),
        )
        assert trust_met.provenance_met()
        assessment_met = evaluate_trust(trust_met)
        assert assessment_met.provenance_met

    def test_evaluate_trust_low_dimensions_reasons(self) -> None:
        trust = DependencyTrust(
            dependency_ref="nav/gnss",
            dimensions=TrustDimensions(
                navigation_integrity=0.2,
                cyber_integrity=0.3,
            ),
            aggregation=TrustAggregation.MINIMUM,
            provenance=TrustProvenance(minimum_independent_sources=1, actual_independent_sources=1),
        )
        assessment = evaluate_trust(trust)
        assert assessment.aggregate_score == 0.2
        assert assessment.weakest_dimension == "navigation_integrity"
        assert any("navigation_integrity critically low" in r for r in assessment.reason_codes)
        assert any("cyber_integrity critically low" in r for r in assessment.reason_codes)
