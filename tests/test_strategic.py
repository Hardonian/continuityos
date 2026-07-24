from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from continuityos.domain import AssertionClass, MetricName, Observation, SourceTrust
from continuityos.strategic import StrategicAnalysisRequest, build_strategic_report


def test_strategic_report_builds_freshness_heatmap_and_advisory_alerts(provenance) -> None:
    now = datetime.now(UTC)
    observations = [
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=value,
            unit="normalized",
            observed_at=now - timedelta(hours=age),
            confidence=confidence,
            provenance=provenance,
        )
        for value, age, confidence in ((0.9, 0, 0.95), (0.7, 3, 0.9))
    ]
    report = build_strategic_report(
        StrategicAnalysisRequest(observations=observations, alert_threshold=0.5)
    )
    assert report.contract_version == "continuityos.strategic-signal.v1"
    assert report.observation_count == 2
    assert report.heatmap[0].dimension == "wind_severity"
    assert report.heatmap[0].freshness > 0.9
    assert report.alerts[0].severity == "critical"
    assert report.coordination[0].approval_required is True
    assert report.predictive_status == "not-run-insufficient-labelled-dataset"
    assert report.regression is None


def test_strategic_report_rejects_non_finite_values(provenance) -> None:
    with pytest.raises(ValueError, match="finite"):
        Observation(
            source_id="eccc-geomet",
            source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
            assertion_class=AssertionClass.WEATHER,
            metric=MetricName.WIND_SEVERITY,
            value=float("nan"),
            unit="normalized",
            observed_at=datetime.now(UTC),
            confidence=0.95,
            provenance=provenance,
        )
