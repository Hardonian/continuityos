from pathlib import Path

import pytest
from httpx import Response

from continuityos.edge import EdgeNode
from continuityos.sources.cache import SnapshotCache


@pytest.fixture
def mock_cache(tmp_path: Path) -> SnapshotCache:
    return SnapshotCache(root=tmp_path / "cache")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_edge_manifest_generation(mock_cache: SnapshotCache) -> None:
    # Populate mock cache
    mock_cache.store("src1", "http://a", b"payload", {}, 200)

    node = EdgeNode(node_id="test-node-1", cache=mock_cache, gossip_interval=10.0)
    manifest = node.get_manifest()

    assert manifest.peer_id == "test-node-1"
    assert len(manifest.snapshot_ids) == 1


@pytest.mark.anyio
async def test_edge_sync_peer(mock_cache: SnapshotCache, monkeypatch: pytest.MonkeyPatch) -> None:
    node = EdgeNode(node_id="test-node-1", cache=mock_cache)
    node.add_peer("http://peer-mock")

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str) -> Response:
            if url.endswith("/manifest"):
                return Response(200, json={"peer_id": "peer-2", "snapshot_ids": ["snap-123"]})
            elif url.endswith("/sync/snap-123"):
                return Response(
                    200,
                    json={
                        "metadata": {
                            "source_id": "mock_src",
                            "url": "http://x",
                            "content_type": "text/plain",
                        },
                        "payload": "mock-payload-data",
                    },
                )
            return Response(404)

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", MockClient)

    # Run sync logic once
    await node._sync_with_peer("http://peer-mock")

    # Verify the snapshot was retrieved and stored
    manifest = node.get_manifest()
    assert len(manifest.snapshot_ids) == 1
    # Check that it stored the snapshot properly
    latest = mock_cache.latest("mock_src")
    assert latest is not None
    _meta, body = latest
    assert body == b"mock-payload-data"
