from __future__ import annotations

import json
from pathlib import Path

import pytest

from continuityos.public_data import PUBLIC_SOURCE_SPECS, PublicDataPlane
from continuityos.sources.cache import SnapshotCache


def test_public_data_plane_requires_allowlisted_source_and_outbound_opt_in(tmp_path: Path) -> None:
    plane = PublicDataPlane(SnapshotCache(tmp_path), outbound_enabled=False)
    with pytest.raises(ValueError, match="not allow-listed"):
        import asyncio

        asyncio.run(plane.fetch("not-allow-listed"))
    with pytest.raises(RuntimeError, match="outbound HTTP disabled"):
        import asyncio

        asyncio.run(plane.fetch("noaa-swpc"))


def test_imported_json_snapshot_is_validated_and_summarized(tmp_path: Path) -> None:
    cache = SnapshotCache(tmp_path)
    path = tmp_path / "payload.json"
    path.write_text(json.dumps({"collections": [{"id": "one"}, {"id": "two"}]}))
    metadata = cache.import_file(
        "copernicus-cdse-stac", PUBLIC_SOURCE_SPECS["copernicus-cdse-stac"].url, path
    )
    plane = PublicDataPlane(cache, outbound_enabled=False)
    snapshot = plane.summarize_snapshot("copernicus-cdse-stac", metadata, path.read_bytes())
    assert snapshot.record_count == 2
    assert snapshot.snapshot_id.startswith("copernicus-cdse-stac-")
    assert "snapshot_cache" in snapshot.quality_flags


def test_top_level_json_array_is_supported(tmp_path: Path) -> None:
    cache = SnapshotCache(tmp_path)
    path = tmp_path / "payload.json"
    path.write_text(json.dumps([{"id": "one"}, {"id": "two"}, {"id": "three"}]))
    metadata = cache.import_file("statcan-wds", PUBLIC_SOURCE_SPECS["statcan-wds"].url, path)
    snapshot = PublicDataPlane(cache, outbound_enabled=False).summarize_snapshot(
        "statcan-wds", metadata, path.read_bytes()
    )
    assert snapshot.record_count == 3


def test_keyed_source_fails_closed_without_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("NASA_FIRMS_MAP_KEY", raising=False)
    plane = PublicDataPlane(SnapshotCache(tmp_path), outbound_enabled=True)
    with pytest.raises(RuntimeError, match="NASA_FIRMS_MAP_KEY"):
        import asyncio

        asyncio.run(plane.fetch("nasa-firms"))


def test_reliefweb_requires_explicit_registered_app_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("RELIEFWEB_APPNAME", raising=False)
    plane = PublicDataPlane(SnapshotCache(tmp_path), outbound_enabled=True)
    with pytest.raises(RuntimeError, match="RELIEFWEB_APPNAME"):
        import asyncio

        asyncio.run(plane.fetch("reliefweb"))
