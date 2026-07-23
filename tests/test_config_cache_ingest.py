from __future__ import annotations

from pathlib import Path

import pytest

from continuityos.config import Settings
from continuityos.ingest import OpenSourceIngestor
from continuityos.sources.cache import SnapshotCache


def test_production_config_fails_closed_without_keys() -> None:
    with pytest.raises(ValueError, match="production configuration missing"):
        Settings(environment="production")


def test_snapshot_cache_is_content_addressed_and_detects_tamper(tmp_path: Path) -> None:
    cache = SnapshotCache(tmp_path)
    source = tmp_path / "input.csv"
    source.write_bytes(b"a,b\n1,2\n")
    metadata = cache.import_file("nsidc-sea-ice-index", "fixture://input", source, "text/csv")
    loaded_metadata, body = cache.read("nsidc-sea-ice-index", metadata.content_sha256)
    assert body == source.read_bytes()
    assert loaded_metadata["snapshot_id"] == metadata.snapshot_id
    payload_path = (
        tmp_path
        / "nsidc-sea-ice-index"
        / metadata.content_sha256[:2]
        / metadata.content_sha256
        / "payload.bin"
    )
    payload_path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        cache.read("nsidc-sea-ice-index", metadata.content_sha256)


def test_geomet_feature_collection_normalization() -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"value": 1}},
            {"type": "invalid"},
        ],
    }
    normalized = OpenSourceIngestor.normalize_geomet_feature_collection(payload)
    assert len(normalized) == 1
    with pytest.raises(ValueError, match="features array"):
        OpenSourceIngestor.normalize_geomet_feature_collection({})


def test_snapshot_first_ingestion_works_offline(tmp_path: Path) -> None:
    import asyncio

    from continuityos.ingest import NSIDC_NORTH_DAILY_EXTENT

    cache = SnapshotCache(tmp_path)
    source = tmp_path / "nsidc.csv"
    source.write_bytes(b"year,month,day,extent\n1981,7,1,10.0\n1982,7,1,8.0\n2026,7,1,7.0\n")
    cache.import_file(
        "nsidc-sea-ice-index",
        NSIDC_NORTH_DAILY_EXTENT,
        source,
        "text/csv",
    )
    ingestor = OpenSourceIngestor(
        cache,
        outbound_enabled=False,
        max_cache_age_hours=24.0,
    )
    observations = asyncio.run(ingestor.nsidc_daily_extent())
    latest = next(item for item in observations if item.observed_at.year == 2026)
    assert latest.value == -2.0
