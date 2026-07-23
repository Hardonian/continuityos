from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from continuityos.domain import AssertionClass, MetricName
from continuityos.sources.adapters import (
    build_copernicus_stac_query,
    parse_celestrak_gp_json,
    parse_nsidc_daily_extent_csv,
)


def test_parse_nsidc_csv() -> None:
    body = b"year,month,day,extent\n1981,7,1,10.0\n1982,7,1,8.0\n2026,7,1,7.0\n"
    observations = parse_nsidc_daily_extent_csv(body, uri="fixture://nsidc")
    latest = next(item for item in observations if item.observed_at.year == 2026)
    assert latest.metric == MetricName.SEA_ICE_EXTENT_ANOMALY
    assert latest.assertion_class == AssertionClass.CLIMATE
    assert latest.value == -2.0
    assert latest.metadata["baseline_period"] == "1981-2010"


def test_celestrak_is_geometry_context_only() -> None:
    body = json.dumps(
        [
            {"OBJECT_ID": "2020-001A", "EPOCH": "2026-07-22T10:00:00Z"},
            {"OBJECT_ID": "2020-001B", "EPOCH": "2026-07-22T11:00:00Z"},
        ]
    ).encode()
    observation = parse_celestrak_gp_json(body, uri="fixture://celestrak")
    assert observation.assertion_class == AssertionClass.ORBITAL_GEOMETRY
    assert observation.metadata["warning"] == "not service availability"
    assert observation.observed_at.hour == 11


def test_stac_query_is_bounded() -> None:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)
    query = build_copernicus_stac_query((-170, 65, -120, 80), start, end)
    assert query["collections"] == ["sentinel-1-grd"]
    assert query["limit"] == 100


def test_stac_query_rejects_invalid_bbox() -> None:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)
    import pytest

    with pytest.raises(ValueError, match="longitude"):
        build_copernicus_stac_query((20, 65, -20, 80), start, end)
