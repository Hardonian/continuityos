from __future__ import annotations

from datetime import UTC, datetime
from math import exp, isfinite
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from continuityos.analysis import RegressionRequest, RegressionResult, run_regression
from continuityos.domain import Observation


class StrategicAnalysisRequest(BaseModel):
    observations: list[Observation] = Field(min_length=1, max_length=10_000)
    regression: RegressionRequest | None = None
    alert_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    freshness_half_life_hours: float = Field(default=24.0, gt=0.0, le=720.0)
    coordination_scope: str = Field(default="operator-review", min_length=2, max_length=128)


class HeatmapCell(BaseModel):
    dimension: str
    source_ids: list[str]
    observation_count: int
    latest_value: float
    normalized_intensity: float
    confidence: float
    freshness: float
    heat_score: float
    quality_flags: list[str]


class StrategicAlert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    dimension: str
    severity: str
    score: float
    rationale: list[str]
    source_ids: list[str]
    requires_human_review: bool = True


class CoordinationRecommendation(BaseModel):
    priority: int
    scope: str
    action: str
    rationale: str
    approval_required: bool = True


class StrategicAnalysisReport(BaseModel):
    contract_version: str = "continuityos.strategic-signal.v1"
    report_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    observation_count: int
    window_start: datetime
    window_end: datetime
    heatmap: list[HeatmapCell]
    alerts: list[StrategicAlert]
    coordination: list[CoordinationRecommendation]
    regression: RegressionResult | None = None
    predictive_status: str
    limitations: list[str]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_strategic_report(request: StrategicAnalysisRequest) -> StrategicAnalysisReport:
    ordered = sorted(request.observations, key=lambda item: item.observed_at.astimezone(UTC))
    if any(not isfinite(item.value) for item in ordered):
        raise ValueError("all observation values must be finite")
    window_start = ordered[0].observed_at
    window_end = ordered[-1].observed_at
    latest = window_end.astimezone(UTC)
    grouped: dict[str, list[Observation]] = {}
    for observation in ordered:
        grouped.setdefault(str(observation.metric), []).append(observation)

    heatmap: list[HeatmapCell] = []
    for dimension, values in sorted(grouped.items()):
        maximum = max(abs(item.value) for item in values) or 1.0
        newest = max(values, key=lambda item: item.observed_at)
        age_hours = max(0.0, (latest - newest.observed_at.astimezone(UTC)).total_seconds() / 3600.0)
        freshness = exp(-age_hours * 0.69314718056 / request.freshness_half_life_hours)
        intensity = _clamp(abs(newest.value) / maximum)
        confidence = _clamp(sum(item.confidence for item in values) / len(values))
        score = _clamp(intensity * confidence * freshness)
        heatmap.append(
            HeatmapCell(
                dimension=dimension,
                source_ids=sorted({item.source_id for item in values}),
                observation_count=len(values),
                latest_value=newest.value,
                normalized_intensity=intensity,
                confidence=confidence,
                freshness=freshness,
                heat_score=score,
                quality_flags=[],
            )
        )

    alerts: list[StrategicAlert] = []
    for cell in heatmap:
        if cell.heat_score < request.alert_threshold:
            continue
        severity = "critical" if cell.heat_score >= 0.85 else "high"
        rationale = [
            (
                f"{cell.dimension} heat score {cell.heat_score:.3f} exceeds threshold "
                f"{request.alert_threshold:.3f}"
            ),
            f"freshness={cell.freshness:.3f}, confidence={cell.confidence:.3f}",
        ]
        if cell.quality_flags:
            rationale.append("quality flags present: " + ", ".join(cell.quality_flags))
        alerts.append(
            StrategicAlert(
                dimension=cell.dimension,
                severity=severity,
                score=cell.heat_score,
                rationale=rationale,
                source_ids=cell.source_ids,
            )
        )
    alerts.sort(key=lambda item: (-item.score, item.dimension))

    coordination = [
        CoordinationRecommendation(
            priority=index,
            scope=request.coordination_scope,
            action=(
                f"Review {alert.dimension} evidence and confirm an owner before "
                "coordinating mitigation"
            ),
            rationale="; ".join(alert.rationale),
        )
        for index, alert in enumerate(alerts, start=1)
    ]

    regression = run_regression(request.regression) if request.regression is not None else None
    predictive_status = (
        "exploratory-temporal-holdout-result"
        if regression is not None
        else "not-run-insufficient-labelled-dataset"
    )
    return StrategicAnalysisReport(
        observation_count=len(ordered),
        window_start=window_start,
        window_end=window_end,
        heatmap=heatmap,
        alerts=alerts,
        coordination=coordination,
        regression=regression,
        predictive_status=predictive_status,
        limitations=[
            "Heat scores are normalized prioritization signals, not probability of failure.",
            "Freshness decay does not correct stale, biased, duplicated, or adversarial sources.",
            (
                "Regression output is associational exploratory analysis with temporal holdout, "
                "not causal inference or a validated forecast."
            ),
            (
                "Recommendations are advisory; human review is required and no action is "
                "executed or dispatched."
            ),
        ],
    )
