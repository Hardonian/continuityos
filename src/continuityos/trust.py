"""Multi-dimensional dependency trust model.

Trust is NOT a single number. A dependency can be physically available but
legally unavailable, commercially available but cyber-compromised, etc. This
module models trust across independent dimensions and provides aggregation
strategies.
"""

from __future__ import annotations

from enum import StrEnum
from statistics import fmean

from pydantic import BaseModel, Field

from continuityos.domain import Score


class TrustAggregation(StrEnum):
    MINIMUM = "minimum"
    WEIGHTED = "weighted"
    MEAN = "mean"


class TrustDimensions(BaseModel):
    """Multi-dimensional trust assessment. Each dimension is independent."""

    physical_availability: Score = 1.0
    cyber_integrity: Score = 1.0
    legal_availability: Score = 1.0
    commercial_availability: Score = 1.0
    insurance_availability: Score = 1.0
    communications_integrity: Score = 1.0
    navigation_integrity: Score = 1.0
    operator_confidence: Score = 1.0
    information_confidence: Score = 1.0

    def all_values(self) -> list[float]:
        return [
            self.physical_availability,
            self.cyber_integrity,
            self.legal_availability,
            self.commercial_availability,
            self.insurance_availability,
            self.communications_integrity,
            self.navigation_integrity,
            self.operator_confidence,
            self.information_confidence,
        ]

    def dimension_names(self) -> list[str]:
        return [
            "physical_availability",
            "cyber_integrity",
            "legal_availability",
            "commercial_availability",
            "insurance_availability",
            "communications_integrity",
            "navigation_integrity",
            "operator_confidence",
            "information_confidence",
        ]

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.dimension_names(), self.all_values(), strict=True))

    def lowest_dimensions(self, n: int = 3) -> list[tuple[str, float]]:
        """Return the N lowest trust dimensions for explainability."""
        pairs = sorted(self.as_dict().items(), key=lambda item: item[1])
        return pairs[:n]


class TrustProvenance(BaseModel):
    minimum_independent_sources: int = Field(default=2, ge=1, le=20)
    actual_independent_sources: int = Field(default=0, ge=0)
    source_ids: list[str] = Field(default_factory=list)


class DependencyTrust(BaseModel):
    """Trust assessment for a single dependency with provenance."""

    dependency_ref: str = Field(min_length=1, max_length=256)
    dimensions: TrustDimensions = Field(default_factory=TrustDimensions)
    aggregation: TrustAggregation = TrustAggregation.MINIMUM
    provenance: TrustProvenance = Field(default_factory=TrustProvenance)

    def aggregate_score(self) -> float:
        """Compute the aggregate trust score using the configured strategy."""
        values = self.dimensions.all_values()
        if self.aggregation == TrustAggregation.MINIMUM:
            return min(values)
        elif self.aggregation == TrustAggregation.MEAN:
            return fmean(values)
        elif self.aggregation == TrustAggregation.WEIGHTED:
            # Weight physical and cyber higher than others
            weights = [0.15, 0.15, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10]
            return sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)
        raise ValueError(f"unknown aggregation: {self.aggregation}")

    def provenance_met(self) -> bool:
        """Check whether minimum independent sources requirement is satisfied."""
        return self.provenance.actual_independent_sources >= self.provenance.minimum_independent_sources

    def weakest_dimension(self) -> tuple[str, float]:
        """Return the name and value of the weakest trust dimension."""
        pairs = self.dimensions.as_dict()
        return min(pairs.items(), key=lambda item: item[1])


class TrustAssessment(BaseModel):
    """Result of evaluating trust across multiple dependencies."""

    dependency_ref: str
    aggregate_score: Score
    weakest_dimension: str
    weakest_value: Score
    provenance_met: bool
    dimension_values: dict[str, float]
    reason_codes: list[str]


def evaluate_trust(trust: DependencyTrust) -> TrustAssessment:
    """Evaluate a DependencyTrust and produce an explainable assessment."""
    score = trust.aggregate_score()
    weakest_name, weakest_value = trust.weakest_dimension()
    reasons: list[str] = []

    if not trust.provenance_met():
        reasons.append(
            f"insufficient independent sources: "
            f"{trust.provenance.actual_independent_sources} < "
            f"{trust.provenance.minimum_independent_sources}"
        )
        score = max(0.0, score * 0.8)  # Penalize low-provenance trust

    low = trust.dimensions.lowest_dimensions(3)
    for dim_name, dim_value in low:
        if dim_value < 0.5:
            reasons.append(f"{dim_name} critically low: {dim_value:.2f}")

    return TrustAssessment(
        dependency_ref=trust.dependency_ref,
        aggregate_score=round(min(1.0, score), 6),
        weakest_dimension=weakest_name,
        weakest_value=round(weakest_value, 6),
        provenance_met=trust.provenance_met(),
        dimension_values=trust.dimensions.as_dict(),
        reason_codes=reasons,
    )
