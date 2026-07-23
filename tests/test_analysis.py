from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from continuityos.analysis import RegressionRequest, RegressionRow, run_regression


def rows(count: int = 12) -> list[RegressionRow]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        RegressionRow(
            observed_at=start + timedelta(days=index),
            target=2.0 + 0.7 * index - 0.2 * (index % 3),
            features={
                "sea_ice": float(index),
                "port_availability": 1.0 - index / 20.0,
                "trade_dependency": 0.2 + index / 30.0,
            },
            source_ids=["nsidc-sea-ice-index", "operator-telemetry"],
            snapshot_ids=[f"snapshot-{index}"],
        )
        for index in range(count)
    ]


def test_temporal_multivariate_regression_has_holdout_and_provenance() -> None:
    result = run_regression(
        RegressionRequest(dataset_id="fixture-dataset", target_name="corridor_delay", rows=rows())
    )
    assert result.train_row_count == 9
    assert result.test_row_count == 3
    assert result.test_start > result.train_end
    assert {item.feature for item in result.coefficients} == {
        "sea_ice",
        "port_availability",
        "trade_dependency",
    }
    assert "operator-telemetry" in result.source_ids
    assert any("not causal" in limitation for limitation in result.limitations)


def test_regression_rejects_schema_drift() -> None:
    sample = rows()
    sample[-1] = sample[-1].model_copy(update={"features": {"sea_ice": 1.0, "other": 2.0}})
    with pytest.raises(ValueError, match="same feature names"):
        run_regression(RegressionRequest(dataset_id="fixture", target_name="target", rows=sample))


def test_regression_requires_timezone_aware_rows() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        RegressionRow(
            observed_at=datetime(2025, 1, 1),
            target=1.0,
            features={"a": 1.0, "b": 2.0},
            source_ids=["source"],
            snapshot_ids=["snapshot"],
        )
