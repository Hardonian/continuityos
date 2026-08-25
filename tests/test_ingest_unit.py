"""Unit tests for Open-Source Ingestor module with mocked dependencies.

Targets: ingest.py coverage from 67% → ≥85%.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from continuityos.ingest import OpenSourceIngestor
from continuityos.sources.cache import SnapshotCache, SnapshotMetadata


def _mock_metadata(source_id: str = "test-source") -> SnapshotMetadata:
    return SnapshotMetadata(
        snapshot_id=f"{source_id}-abc123",
        source_id=source_id,
        url="https://example.com/data",
        retrieved_at=datetime.now(UTC).isoformat(),
        content_sha256="a" * 64,
        content_type="application/json",
        etag=None,
        last_modified=None,
        status_code=200,
    )


class TestGetOrFetch:
    """Test the cache-first fetch logic."""

    def test_returns_cached_when_available(self) -> None:
        cache = MagicMock(spec=SnapshotCache)
        metadata = _mock_metadata()
        cache.latest.return_value = (metadata, b"cached-body")

        ingestor = OpenSourceIngestor(cache, outbound_enabled=False)

        async def run() -> tuple[SnapshotMetadata, bytes]:
            return await ingestor._get_or_fetch("test-source", "https://example.com/data")

        _result_meta, result_body = asyncio.get_event_loop().run_until_complete(run())
        assert result_body == b"cached-body"
        cache.fetch.assert_not_called()

    def test_fetches_when_not_cached(self) -> None:
        cache = MagicMock(spec=SnapshotCache)
        cache.latest.return_value = None
        metadata = _mock_metadata()
        cache.fetch = AsyncMock(return_value=(metadata, b"fresh-body"))

        ingestor = OpenSourceIngestor(cache, outbound_enabled=True)

        async def run() -> tuple[SnapshotMetadata, bytes]:
            return await ingestor._get_or_fetch("test-source", "https://example.com/data")

        _result_meta, result_body = asyncio.get_event_loop().run_until_complete(run())
        assert result_body == b"fresh-body"
        cache.fetch.assert_called_once()


class TestNSIDCDailyExtent:
    """Test NSIDC sea ice extent ingestion."""

    def test_parses_cached_csv(self) -> None:
        csv_data = (
            "Year, Month, Day, Extent, Missing, Source Data, Hemisphere\n"
            "1981, 1, 1, 13.5, 0.0, nsidc, north\n"
            "1981, 1, 2, 13.6, 0.0, nsidc, north\n"
            "2024, 1, 1, 12.0, 0.0, nsidc, north\n"
            "2024, 1, 2, 12.1, 0.0, nsidc, north\n"
        )
        cache = MagicMock(spec=SnapshotCache)
        metadata = _mock_metadata("nsidc-sea-ice-index")
        cache.latest.return_value = (metadata, csv_data.encode("utf-8"))

        ingestor = OpenSourceIngestor(cache, outbound_enabled=False)

        observations = asyncio.get_event_loop().run_until_complete(ingestor.nsidc_daily_extent())
        # Only dates with baseline values (1981 data provides baseline for Jan 1 and Jan 2)
        assert len(observations) >= 2


class TestCelestrakGeometry:
    """Test CelesTrak satellite geometry ingestion."""

    def test_parses_cached_gp_json(self) -> None:
        records = [
            {"OBJECT_ID": "STARLINK-1", "EPOCH": "2024-01-15T12:00:00+00:00"},
            {"OBJECT_ID": "STARLINK-2", "EPOCH": "2024-01-15T13:00:00+00:00"},
        ]
        body = json.dumps(records).encode("utf-8")

        cache = MagicMock(spec=SnapshotCache)
        metadata = _mock_metadata("celestrak-gp")
        cache.latest.return_value = (metadata, body)

        ingestor = OpenSourceIngestor(cache, outbound_enabled=False)

        observation = asyncio.get_event_loop().run_until_complete(
            ingestor.celestrak_geometry("starlink")
        )
        assert observation.source_id == "celestrak-gp"
        assert observation.value == 2.0


class TestCopernicusSTAC:
    """Test Copernicus STAC ingestion paths."""

    def test_returns_cached_stac_response(self) -> None:
        stac_response = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"datetime": "2024-01-15T10:00:00Z"},
                    "geometry": {"type": "Point", "coordinates": [-73.0, 45.0]},
                }
            ],
        }
        body = json.dumps(stac_response).encode("utf-8")

        cache = MagicMock(spec=SnapshotCache)
        metadata = _mock_metadata("copernicus-cdse-stac")
        cache.latest.return_value = (metadata, body)

        ingestor = OpenSourceIngestor(cache, outbound_enabled=False)

        observation = asyncio.get_event_loop().run_until_complete(
            ingestor.copernicus_stac(
                bbox=(-80.0, 40.0, -70.0, 50.0),
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 31, tzinfo=UTC),
            )
        )
        assert observation.source_id == "copernicus-cdse-stac"
        assert observation.value == 1.0

    def test_raises_when_outbound_disabled_and_no_cache(self) -> None:
        cache = MagicMock(spec=SnapshotCache)
        cache.latest.return_value = None

        ingestor = OpenSourceIngestor(cache, outbound_enabled=False)

        with pytest.raises(RuntimeError, match="outbound HTTP disabled"):
            asyncio.get_event_loop().run_until_complete(
                ingestor.copernicus_stac(
                    bbox=(-80.0, 40.0, -70.0, 50.0),
                    start=datetime(2024, 1, 1, tzinfo=UTC),
                    end=datetime(2024, 1, 31, tzinfo=UTC),
                )
            )


class TestNormalizeGeometFeatureCollection:
    """Test GeoMet feature collection normalization."""

    def test_valid_feature_collection(self) -> None:
        payload: dict[str, Any] = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"station": "YOW"}},
                {"type": "Feature", "properties": {"station": "YUL"}},
                {"type": "NotAFeature", "properties": {}},  # should be filtered
            ],
        }
        result = OpenSourceIngestor.normalize_geomet_feature_collection(payload)
        assert len(result) == 2

    def test_missing_features_array(self) -> None:
        with pytest.raises(ValueError, match="missing features array"):
            OpenSourceIngestor.normalize_geomet_feature_collection({"type": "FeatureCollection"})

    def test_features_not_list(self) -> None:
        with pytest.raises(ValueError, match="missing features array"):
            OpenSourceIngestor.normalize_geomet_feature_collection({"features": "not_a_list"})

    def test_non_dict_features_skipped(self) -> None:
        payload: dict[str, Any] = {
            "features": [
                {"type": "Feature", "properties": {}},
                "not-a-dict",
                42,
            ],
        }
        result = OpenSourceIngestor.normalize_geomet_feature_collection(payload)
        assert len(result) == 1
