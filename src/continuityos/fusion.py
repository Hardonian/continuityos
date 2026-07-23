from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from statistics import fmean
from typing import ClassVar

from continuityos.domain import (
    CorridorAssessment,
    CorridorFactor,
    CorridorState,
    FactorAssessment,
    MetricName,
    Observation,
)
from continuityos.sources.policy import validate_observation_source


class FusionPolicy:
    """Deterministic mapping from normalized metrics to corridor risk factors."""

    REQUIRED_METRICS: frozenset[MetricName] = frozenset(
        {
            MetricName.SEA_ICE_CONCENTRATION,
            MetricName.WIND_SEVERITY,
            MetricName.PORT_AVAILABILITY,
            MetricName.SATCOM_AVAILABILITY,
            MetricName.CYBER_CONTROL_HEALTH,
            MetricName.DATA_INTEGRITY,
            MetricName.INSURANCE_AVAILABILITY,
            MetricName.ESCORT_CAPACITY,
            MetricName.INVENTORY_DAYS,
        }
    )

    CONTEXT_ONLY_METRICS: frozenset[MetricName] = frozenset(
        {
            MetricName.SEA_ICE_EXTENT_ANOMALY,
            MetricName.EARTH_OBSERVATION_COVERAGE,
            MetricName.SATELLITE_GEOMETRY_DENSITY,
            MetricName.PORT_GEOMETRY,
        }
    )

    METRIC_TO_FACTOR: ClassVar[dict[MetricName, CorridorFactor]] = {
        MetricName.SEA_ICE_CONCENTRATION: CorridorFactor.ICE,
        MetricName.WIND_SEVERITY: CorridorFactor.WEATHER,
        MetricName.WAVE_SEVERITY: CorridorFactor.WEATHER,
        MetricName.AIS_TRAFFIC_INDEX: CorridorFactor.TRAFFIC,
        MetricName.PORT_CAPACITY: CorridorFactor.PORT,
        MetricName.PORT_AVAILABILITY: CorridorFactor.PORT,
        MetricName.SATCOM_AVAILABILITY: CorridorFactor.COMMUNICATIONS,
        MetricName.CYBER_CONTROL_HEALTH: CorridorFactor.CYBER,
        MetricName.DATA_INTEGRITY: CorridorFactor.DATA_TRUST,
        MetricName.INSURANCE_AVAILABILITY: CorridorFactor.COMMERCIAL,
        MetricName.GEOPOLITICAL_PRESSURE: CorridorFactor.GEOPOLITICAL,
        MetricName.ESCORT_CAPACITY: CorridorFactor.ESCORT,
        MetricName.INVENTORY_DAYS: CorridorFactor.INVENTORY,
        MetricName.TRADE_DEPENDENCY: CorridorFactor.COMMERCIAL,
    }

    MAX_AGE_HOURS: ClassVar[dict[MetricName, float]] = {
        MetricName.SEA_ICE_CONCENTRATION: 24.0,
        MetricName.SEA_ICE_EXTENT_ANOMALY: 24.0 * 14,
        MetricName.EARTH_OBSERVATION_COVERAGE: 24.0 * 7,
        MetricName.WIND_SEVERITY: 12.0,
        MetricName.WAVE_SEVERITY: 12.0,
        MetricName.AIS_TRAFFIC_INDEX: 24.0 * 30,
        MetricName.PORT_CAPACITY: 2.0,
        MetricName.PORT_AVAILABILITY: 2.0,
        MetricName.SATCOM_AVAILABILITY: 1.0,
        MetricName.SATELLITE_GEOMETRY_DENSITY: 24.0 * 7,
        MetricName.CYBER_CONTROL_HEALTH: 1.0,
        MetricName.DATA_INTEGRITY: 1.0,
        MetricName.INSURANCE_AVAILABILITY: 24.0,
        MetricName.GEOPOLITICAL_PRESSURE: 24.0 * 7,
        MetricName.ESCORT_CAPACITY: 6.0,
        MetricName.INVENTORY_DAYS: 24.0,
        MetricName.TRADE_DEPENDENCY: 24.0 * 90,
        MetricName.PORT_GEOMETRY: 24.0 * 365,
    }

    FACTOR_WEIGHTS: ClassVar[dict[CorridorFactor, float]] = {
        CorridorFactor.ICE: 0.14,
        CorridorFactor.WEATHER: 0.08,
        CorridorFactor.TRAFFIC: 0.06,
        CorridorFactor.PORT: 0.12,
        CorridorFactor.COMMUNICATIONS: 0.11,
        CorridorFactor.CYBER: 0.12,
        CorridorFactor.DATA_TRUST: 0.10,
        CorridorFactor.COMMERCIAL: 0.09,
        CorridorFactor.GEOPOLITICAL: 0.07,
        CorridorFactor.ESCORT: 0.06,
        CorridorFactor.INVENTORY: 0.05,
    }

    @staticmethod
    def _bounded(value: float) -> float:
        return min(1.0, max(0.0, value))

    @classmethod
    def metric_risk(cls, observation: Observation) -> float:
        value = observation.value
        metric = observation.metric
        transforms: dict[MetricName, Callable[[float], float]] = {
            MetricName.SEA_ICE_CONCENTRATION: lambda x: x / 100.0 if x > 1 else x,
            MetricName.WIND_SEVERITY: lambda x: x,
            MetricName.WAVE_SEVERITY: lambda x: x,
            MetricName.AIS_TRAFFIC_INDEX: lambda x: 1.0 - x,
            MetricName.PORT_CAPACITY: lambda x: 1.0 - x,
            MetricName.PORT_AVAILABILITY: lambda x: 1.0 - x,
            MetricName.SATCOM_AVAILABILITY: lambda x: 1.0 - x,
            MetricName.CYBER_CONTROL_HEALTH: lambda x: 1.0 - x,
            MetricName.DATA_INTEGRITY: lambda x: 1.0 - x,
            MetricName.INSURANCE_AVAILABILITY: lambda x: 1.0 - x,
            MetricName.GEOPOLITICAL_PRESSURE: lambda x: x,
            MetricName.ESCORT_CAPACITY: lambda x: 1.0 - x,
            MetricName.INVENTORY_DAYS: lambda x: 1.0 - min(x / 45.0, 1.0),
            MetricName.TRADE_DEPENDENCY: lambda x: x,
        }
        return cls._bounded(transforms[metric](value))


class FusionEngine:
    def __init__(self, policy: type[FusionPolicy] = FusionPolicy) -> None:
        self.policy = policy

    def assess(
        self,
        corridor_id: str,
        observations: list[Observation],
        *,
        as_of: datetime | None = None,
    ) -> CorridorAssessment:
        if not observations:
            raise ValueError("at least one observation is required")
        now = as_of or datetime.now(UTC)
        if now.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        valid: list[Observation] = []
        caveats: list[str] = []
        for observation in observations:
            validate_observation_source(observation)
            if observation.observed_at > now:
                caveats.append(f"future observation excluded: {observation.observation_id}")
                continue
            if observation.valid_until is not None and observation.valid_until < now:
                caveats.append(f"expired observation excluded: {observation.observation_id}")
                continue
            age_hours = (now - observation.observed_at).total_seconds() / 3600.0
            maximum_age = self.policy.MAX_AGE_HOURS[observation.metric]
            if age_hours > maximum_age:
                caveats.append(
                    f"stale observation excluded: {observation.observation_id} "
                    f"({age_hours:.1f}h > {maximum_age:.1f}h)"
                )
                continue
            valid.append(observation)
        if not valid:
            raise ValueError("no current observations remain after validation")

        grouped: dict[CorridorFactor, list[Observation]] = defaultdict(list)
        present_metrics: set[MetricName] = set()
        context_metrics: list[MetricName] = []
        for observation in valid:
            if observation.metric in self.policy.CONTEXT_ONLY_METRICS:
                context_metrics.append(observation.metric)
                continue
            grouped[self.policy.METRIC_TO_FACTOR[observation.metric]].append(observation)
            present_metrics.add(observation.metric)

        missing = sorted(
            self.policy.REQUIRED_METRICS - present_metrics,
            key=lambda item: item.value,
        )
        factor_assessments: list[FactorAssessment] = []
        weighted_risk = 0.0
        weight_used = 0.0
        confidence_values: list[float] = []

        for factor in CorridorFactor:
            items = grouped.get(factor, [])
            if not items:
                continue
            weighted_items = []
            total_confidence = 0.0
            for item in items:
                freshness = self._freshness(
                    item.observed_at, now, self.policy.MAX_AGE_HOURS[item.metric]
                )
                effective_confidence = item.confidence * freshness
                weighted_items.append((self.policy.metric_risk(item), effective_confidence))
                total_confidence += effective_confidence
            if total_confidence == 0:
                risk = 0.5
                factor_confidence = 0.0
            else:
                risk = sum(r * c for r, c in weighted_items) / total_confidence
                factor_confidence = min(1.0, total_confidence / len(weighted_items))
            assessment = FactorAssessment(
                factor=factor,
                risk=round(risk, 6),
                confidence=round(factor_confidence, 6),
                evidence_ids=[item.observation_id for item in items],
                rationale=self._rationale(factor, items, risk),
            )
            factor_assessments.append(assessment)
            factor_weight = self.policy.FACTOR_WEIGHTS[factor]
            weighted_risk += risk * factor_weight
            weight_used += factor_weight
            confidence_values.append(factor_confidence)

        base_risk = weighted_risk / weight_used if weight_used else 0.5
        missing_penalty = min(0.25, len(missing) * 0.025)
        low_confidence_penalty = (
            (1.0 - fmean(confidence_values)) * 0.10 if confidence_values else 0.10
        )
        overall_risk = min(1.0, base_risk + missing_penalty + low_confidence_penalty)
        mean_confidence = fmean(confidence_values) if confidence_values else 0.0
        confidence = max(0.0, mean_confidence - missing_penalty)

        state = self._classify(overall_risk, grouped)
        if context_metrics:
            caveats.append(
                "context-only metrics excluded from live operability score: "
                + ", ".join(sorted({metric.value for metric in context_metrics}))
            )
        if missing:
            caveats.append(
                "required metrics absent: " + ", ".join(metric.value for metric in missing)
            )
        caveats.append(
            "public geospatial, orbital and port datasets cannot establish live cyber, capacity, "
            "insurance or service availability"
        )
        return CorridorAssessment(
            corridor_id=corridor_id,
            overall_risk=round(overall_risk, 6),
            confidence=round(confidence, 6),
            state=state,
            factors=sorted(factor_assessments, key=lambda item: item.factor.value),
            missing_required_metrics=missing,
            caveats=caveats,
        )

    @staticmethod
    def _freshness(observed_at: datetime, now: datetime, maximum_age_hours: float) -> float:
        age_hours = max(0.0, (now - observed_at).total_seconds() / 3600.0)
        half_life = max(0.25, maximum_age_hours / 2.0)
        return math.exp(-math.log(2.0) * age_hours / half_life)

    @staticmethod
    def _rationale(factor: CorridorFactor, items: list[Observation], risk: float) -> str:
        metrics = sorted({item.metric.value for item in items})
        return f"{factor.value} risk {risk:.3f} derived from {', '.join(metrics)}"

    @staticmethod
    def _classify(
        overall_risk: float, grouped: dict[CorridorFactor, list[Observation]]
    ) -> CorridorState:
        port_values = [
            item.value
            for item in grouped.get(CorridorFactor.PORT, [])
            if item.metric == MetricName.PORT_AVAILABILITY
        ]
        if port_values and max(port_values) <= 0.01:
            return CorridorState.PHYSICALLY_CLOSED
        if overall_risk >= 0.72:
            return CorridorState.FUNCTIONALLY_CLOSED
        if overall_risk >= 0.38:
            return CorridorState.DEGRADED
        return CorridorState.OPEN
