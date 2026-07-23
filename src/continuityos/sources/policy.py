from __future__ import annotations

from continuityos.domain import AssertionClass, MetricName, Observation, SourceTrust
from continuityos.sources.registry import get_source


class SourcePolicyError(ValueError):
    """Raised when a source is used to make an assertion it cannot support."""


METRIC_ASSERTIONS: dict[MetricName, frozenset[AssertionClass]] = {
    MetricName.SEA_ICE_CONCENTRATION: frozenset({AssertionClass.ICE}),
    MetricName.SEA_ICE_EXTENT_ANOMALY: frozenset({AssertionClass.CLIMATE}),
    MetricName.EARTH_OBSERVATION_COVERAGE: frozenset({AssertionClass.EARTH_OBSERVATION}),
    MetricName.WIND_SEVERITY: frozenset({AssertionClass.WEATHER}),
    MetricName.WAVE_SEVERITY: frozenset({AssertionClass.WEATHER}),
    MetricName.PORT_GEOMETRY: frozenset({AssertionClass.GEOLOCATION}),
    MetricName.PORT_CAPACITY: frozenset({AssertionClass.LIVE_CAPACITY}),
    MetricName.PORT_AVAILABILITY: frozenset({AssertionClass.LIVE_AVAILABILITY}),
    MetricName.AIS_TRAFFIC_INDEX: frozenset({AssertionClass.TRAFFIC_HISTORY}),
    MetricName.TRADE_DEPENDENCY: frozenset({AssertionClass.TRADE_EXPOSURE}),
    MetricName.SATELLITE_GEOMETRY_DENSITY: frozenset({AssertionClass.ORBITAL_GEOMETRY}),
    MetricName.SATCOM_AVAILABILITY: frozenset({AssertionClass.LIVE_AVAILABILITY}),
    MetricName.CYBER_CONTROL_HEALTH: frozenset({AssertionClass.CYBER_HEALTH}),
    MetricName.DATA_INTEGRITY: frozenset({AssertionClass.CYBER_HEALTH}),
    MetricName.INSURANCE_AVAILABILITY: frozenset({AssertionClass.INSURANCE_ACCESS}),
    MetricName.GEOPOLITICAL_PRESSURE: frozenset({AssertionClass.GEOPOLITICAL_CONTEXT}),
    MetricName.ESCORT_CAPACITY: frozenset({AssertionClass.LIVE_CAPACITY}),
    MetricName.INVENTORY_DAYS: frozenset({AssertionClass.LIVE_CAPACITY}),
}


def validate_observation_source(observation: Observation) -> None:
    source = get_source(observation.source_id)
    if observation.source_trust != source.trust:
        raise SourcePolicyError(
            f"source trust mismatch for {observation.source_id}: "
            f"expected {source.trust}, got {observation.source_trust}"
        )
    if observation.assertion_class not in source.allowed_assertions:
        raise SourcePolicyError(
            f"{observation.source_id} cannot assert {observation.assertion_class}; "
            f"allowed={sorted(item.value for item in source.allowed_assertions)}"
        )
    metric_assertions = METRIC_ASSERTIONS[observation.metric]
    if observation.assertion_class not in metric_assertions:
        raise SourcePolicyError(
            f"metric {observation.metric} is incompatible with assertion "
            f"{observation.assertion_class}; allowed="
            f"{sorted(item.value for item in metric_assertions)}"
        )
    if observation.source_trust == SourceTrust.ANALYST_ASSESSMENT:
        judgment_type = observation.metadata.get("judgment_type")
        basis = observation.metadata.get("basis")
        if judgment_type not in {"observed_fact", "analytic_judgment", "scenario"}:
            raise SourcePolicyError(
                "analyst assessments require metadata.judgment_type as observed_fact, "
                "analytic_judgment, or scenario"
            )
        if not isinstance(basis, str) or not basis.strip():
            raise SourcePolicyError("analyst assessments require non-empty metadata.basis")
