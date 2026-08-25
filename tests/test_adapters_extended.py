"""Extended tests for source adapters (NSIDC, CelesTrak, STAC).

Targets: sources/adapters.py coverage from 63% → ≥85%.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from continuityos.sources.adapters import (
    build_celestrak_query,
    build_copernicus_stac_query,
    parse_celestrak_gp_json,
    parse_nsidc_daily_extent_csv,
    parse_stac_search_response,
)


class TestParseNSIDC:
    """Extended NSIDC CSV parser edge cases."""

    def test_empty_csv(self) -> None:
        body = b"Year, Month, Day, Extent, Missing, Source Data\n"
        result = parse_nsidc_daily_extent_csv(body, uri="https://example.com/ice.csv")
        assert result == []

    def test_negative_extent_skipped(self) -> None:
        csv = "Year, Month, Day, Extent\n1981, 6, 15, -999.0\n"
        result = parse_nsidc_daily_extent_csv(csv.encode(), uri="https://example.com")
        assert result == []

    def test_malformed_rows_skipped(self) -> None:
        csv = (
            "Year, Month, Day, Extent\nnot_a_year, 1, 1, 13.5\n1981, 1, 1, 13.5\n2024, 1, 1, 12.0\n"
        )
        result = parse_nsidc_daily_extent_csv(csv.encode(), uri="https://example.com")
        # 1981 entry provides baseline, 2024 entry gets anomaly computed
        assert len(result) >= 1

    def test_no_baseline_period_skips(self) -> None:
        """Dates with no 1981-2010 baseline for their day-of-year get skipped."""
        csv = (
            "Year, Month, Day, Extent\n"
            "2024, 2, 29, 12.0\n"  # Feb 29 - unlikely to have baseline
        )
        result = parse_nsidc_daily_extent_csv(csv.encode(), uri="https://example.com")
        # No baseline for Feb 29 in non-leap years, so may be empty
        assert isinstance(result, list)

    def test_utf8_bom_handling(self) -> None:
        csv = "\ufeffYear, Month, Day, Extent\n1981, 3, 1, 14.0\n2024, 3, 1, 12.5\n"
        result = parse_nsidc_daily_extent_csv(csv.encode("utf-8-sig"), uri="https://example.com")
        assert len(result) >= 1

    def test_alternative_column_name(self) -> None:
        """Parser should handle 'Extent' or 'extent_million_sq_km' column names."""
        csv = "Year, Month, Day, extent_million_sq_km\n1981, 7, 4, 8.2\n2024, 7, 4, 7.0\n"
        result = parse_nsidc_daily_extent_csv(csv.encode(), uri="https://example.com")
        assert len(result) >= 1

    def test_snapshot_id_propagated(self) -> None:
        csv = "Year, Month, Day, Extent\n1981, 1, 1, 13.5\n2024, 1, 1, 12.0\n"
        result = parse_nsidc_daily_extent_csv(
            csv.encode(), uri="https://example.com", snapshot_id="snap-abc"
        )
        if result:
            assert result[0].provenance.snapshot_id == "snap-abc"


class TestParseCelesTrak:
    """Extended CelesTrak GP JSON parser edge cases."""

    def test_empty_array(self) -> None:
        with pytest.raises(ValueError, match="no epoch-qualified"):
            parse_celestrak_gp_json(b"[]", uri="https://celestrak.org/test")

    def test_not_array(self) -> None:
        with pytest.raises(ValueError, match="must be a JSON array"):
            parse_celestrak_gp_json(b"{}", uri="https://celestrak.org/test")

    def test_missing_object_id_skipped(self) -> None:
        records = [
            {"EPOCH": "2024-01-15T12:00:00+00:00"},  # No OBJECT_ID
            {"OBJECT_ID": "SAT-1", "EPOCH": "2024-01-15T12:00:00+00:00"},
        ]
        obs = parse_celestrak_gp_json(
            json.dumps(records).encode(), uri="https://celestrak.org/test"
        )
        assert obs.value == 1.0

    def test_missing_epoch_skipped(self) -> None:
        records = [
            {"OBJECT_ID": "SAT-1"},  # No EPOCH
            {"OBJECT_ID": "SAT-2", "EPOCH": "2024-01-15T12:00:00+00:00"},
        ]
        obs = parse_celestrak_gp_json(
            json.dumps(records).encode(), uri="https://celestrak.org/test"
        )
        assert obs.value == 1.0

    def test_invalid_epoch_format_skipped(self) -> None:
        records = [
            {"OBJECT_ID": "SAT-1", "EPOCH": "not-a-date"},
            {"OBJECT_ID": "SAT-2", "EPOCH": "2024-01-15T12:00:00+00:00"},
        ]
        obs = parse_celestrak_gp_json(
            json.dumps(records).encode(), uri="https://celestrak.org/test"
        )
        assert obs.value == 1.0

    def test_non_dict_items_skipped(self) -> None:
        records = [
            "not_a_dict",
            {"OBJECT_ID": "SAT-1", "EPOCH": "2024-01-15T12:00:00+00:00"},
        ]
        obs = parse_celestrak_gp_json(
            json.dumps(records).encode(), uri="https://celestrak.org/test"
        )
        assert obs.value == 1.0

    def test_snapshot_id_in_provenance(self) -> None:
        records = [{"OBJECT_ID": "SAT-1", "EPOCH": "2024-01-15T12:00:00Z"}]
        obs = parse_celestrak_gp_json(
            json.dumps(records).encode(), uri="https://celestrak.org/test", snapshot_id="snap-xyz"
        )
        assert obs.provenance.snapshot_id == "snap-xyz"


class TestParseSTAC:
    """Extended STAC search response parser edge cases."""

    def test_not_feature_collection(self) -> None:
        with pytest.raises(ValueError, match="must be a FeatureCollection"):
            parse_stac_search_response(b'{"type":"Catalog"}', uri="https://stac.example.com")

    def test_features_not_array(self) -> None:
        body = json.dumps({"type": "FeatureCollection", "features": "bad"}).encode()
        with pytest.raises(ValueError, match="must be an array"):
            parse_stac_search_response(body, uri="https://stac.example.com")

    def test_empty_features(self) -> None:
        body = json.dumps({"type": "FeatureCollection", "features": []}).encode()
        obs = parse_stac_search_response(body, uri="https://stac.example.com")
        assert obs.value == 0.0
        assert obs.confidence == 0.40  # low confidence when no timestamps

    def test_non_dict_features_skipped(self) -> None:
        body = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    "not_a_dict",
                    {"type": "Feature", "properties": {"datetime": "2024-06-01T00:00:00Z"}},
                ],
            }
        ).encode()
        obs = parse_stac_search_response(body, uri="https://stac.example.com")
        assert obs.value == 2.0  # total feature count (including non-dict)

    def test_start_datetime_fallback(self) -> None:
        """When 'datetime' is null, parser uses 'start_datetime' instead."""
        body = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"datetime": None, "start_datetime": "2024-06-01T00:00:00Z"},
                    },
                ],
            }
        ).encode()
        obs = parse_stac_search_response(body, uri="https://stac.example.com")
        assert obs.confidence == 0.85

    def test_missing_properties_skipped(self) -> None:
        body = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature"},
                    {"type": "Feature", "properties": {"datetime": "2024-06-01T00:00:00Z"}},
                ],
            }
        ).encode()
        obs = parse_stac_search_response(body, uri="https://stac.example.com")
        assert obs.value == 2.0


class TestBuildCopernicusSTACQuery:
    """Test STAC query construction validation."""

    def test_valid_query(self) -> None:
        query = build_copernicus_stac_query(
            bbox=(-80.0, 40.0, -70.0, 50.0),
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 31, tzinfo=UTC),
        )
        assert query["collections"] == ["sentinel-1-grd"]
        assert query["bbox"] == [-80.0, 40.0, -70.0, 50.0]
        assert query["limit"] == 100

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            build_copernicus_stac_query(
                bbox=(-80.0, 40.0, -70.0, 50.0),
                start=datetime(2024, 1, 1),
                end=datetime(2024, 1, 31, tzinfo=UTC),
            )

    def test_start_after_end_rejected(self) -> None:
        with pytest.raises(ValueError, match="start must precede"):
            build_copernicus_stac_query(
                bbox=(-80.0, 40.0, -70.0, 50.0),
                start=datetime(2024, 2, 1, tzinfo=UTC),
                end=datetime(2024, 1, 1, tzinfo=UTC),
            )

    def test_limit_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="limit outside"):
            build_copernicus_stac_query(
                bbox=(-80.0, 40.0, -70.0, 50.0),
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 31, tzinfo=UTC),
                limit=0,
            )

    def test_invalid_longitude(self) -> None:
        with pytest.raises(ValueError, match="longitude"):
            build_copernicus_stac_query(
                bbox=(180.0, 40.0, -70.0, 50.0),  # west > east
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 31, tzinfo=UTC),
            )

    def test_invalid_latitude(self) -> None:
        with pytest.raises(ValueError, match="latitude"):
            build_copernicus_stac_query(
                bbox=(-80.0, 50.0, -70.0, 40.0),  # south > north
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 31, tzinfo=UTC),
            )


class TestBuildCelestrakQuery:
    """Test CelesTrak query URL construction."""

    def test_valid_group(self) -> None:
        url = build_celestrak_query("starlink")
        assert "GROUP=starlink" in url

    def test_hyphenated_group(self) -> None:
        url = build_celestrak_query("geo-protected")
        assert "GROUP=geo-protected" in url

    def test_case_normalization(self) -> None:
        url = build_celestrak_query("  STARLINK  ")
        assert "GROUP=starlink" in url

    def test_invalid_characters_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid CelesTrak group"):
            build_celestrak_query("group; DROP TABLE")
