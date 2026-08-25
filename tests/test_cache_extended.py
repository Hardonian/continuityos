"""Extended unit tests for SnapshotCache module.

Targets: sources/cache.py coverage from 83% → 100%.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from continuityos.sources.cache import SnapshotCache

pytestmark = pytest.mark.anyio


def test_cache_atomic_write_collision_error(tmp_path: Path) -> None:
    """When a file already exists with DIFFERENT content, raise ValueError."""
    cache = SnapshotCache(tmp_path)
    target = tmp_path / "test.bin"
    target.write_bytes(b"original")

    with pytest.raises(ValueError, match="immutable snapshot collision"):
        cache._atomic_write(target, b"different")


def test_cache_atomic_write_idempotent_when_same_content(tmp_path: Path) -> None:
    """When a file already exists with SAME content, no error is raised."""
    cache = SnapshotCache(tmp_path)
    target = tmp_path / "test.bin"
    target.write_bytes(b"same-data")

    # Should not raise
    cache._atomic_write(target, b"same-data")
    assert target.read_bytes() == b"same-data"


async def test_cache_fetch_outbound_disabled(tmp_path: Path) -> None:
    """When outbound_enabled is False, fetch raises RuntimeError."""
    cache = SnapshotCache(tmp_path)
    with pytest.raises(RuntimeError, match="outbound HTTP disabled"):
        await cache.fetch("source-1", "https://example.com/data", outbound_enabled=False)


async def test_cache_fetch_success(tmp_path: Path) -> None:
    """Successful fetch downloads content, stores it, and returns metadata."""
    cache = SnapshotCache(tmp_path)

    mock_resp = AsyncMock()
    mock_resp.content = b"downloaded-data"
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        metadata, body = await cache.fetch(
            "source-1", "https://example.com/data", outbound_enabled=True
        )

    assert body == b"downloaded-data"
    assert metadata.source_id == "source-1"
    assert metadata.status_code == 200


def test_cache_latest_url_filter(tmp_path: Path) -> None:
    """latest() filters by URL correctly."""
    cache = SnapshotCache(tmp_path)
    f1 = tmp_path / "f1.txt"
    f1.write_bytes(b"data-1")
    f2 = tmp_path / "f2.txt"
    f2.write_bytes(b"data-2")

    cache.import_file("src-multi", "https://example.com/a", f1)
    cache.import_file("src-multi", "https://example.com/b", f2)

    found = cache.latest("src-multi", url="https://example.com/b")
    assert found is not None
    meta, body = found
    assert body == b"data-2"
    assert meta.url == "https://example.com/b"


def test_cache_latest_max_age_filter(tmp_path: Path) -> None:
    """latest() filters out snapshots older than max_age_hours."""
    cache = SnapshotCache(tmp_path)
    f = tmp_path / "f.txt"
    f.write_bytes(b"old-data")

    meta = cache.import_file("src-age", "https://example.com/old", f)

    # Corrupt or modify timestamp in metadata file to simulate an old snapshot
    digest = meta.content_sha256
    meta_path = tmp_path / "src-age" / digest[:2] / digest / "metadata.json"
    meta_path.write_text(
        meta_path.read_text().replace(meta.retrieved_at, "2020-01-01T00:00:00+00:00")
    )

    # Should be None when max_age_hours is small
    found = cache.latest("src-age", max_age_hours=1.0)
    assert found is None


def test_cache_latest_corrupt_metadata_skipped(tmp_path: Path) -> None:
    """Corrupt metadata files are skipped gracefully."""
    cache = SnapshotCache(tmp_path)
    f = tmp_path / "f.txt"
    f.write_bytes(b"valid-data")

    meta = cache.import_file("src-corrupt", "https://example.com/data", f)

    # Write garbage to metadata.json
    digest = meta.content_sha256
    meta_path = tmp_path / "src-corrupt" / digest[:2] / digest / "metadata.json"
    meta_path.write_text("NOT_JSON")

    found = cache.latest("src-corrupt")
    assert found is None


def test_cache_latest_nonexistent_source_returns_none(tmp_path: Path) -> None:
    """Non-existent source returns None."""
    cache = SnapshotCache(tmp_path)
    assert cache.latest("nonexistent") is None
