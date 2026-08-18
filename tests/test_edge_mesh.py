from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from httpx import Response

from continuityos.edge import EdgeNode
from continuityos.sources.cache import SnapshotCache


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_edge_node_mesh_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = SnapshotCache(root=tmp_path)
    node = EdgeNode(node_id="test-edge-node-alpha", cache=cache, gossip_interval=0.1)

    # 1. Manifest generation
    manifest = node.get_manifest()
    assert manifest.peer_id == "test-edge-node-alpha"
    assert isinstance(manifest.snapshot_ids, list)

    # 2. Add peer
    node.add_peer("http://127.0.0.1:18998")
    assert "http://127.0.0.1:18998" in node.peers

    # 3. Process sync
    class MockGossipClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str) -> Response:
            import httpx

            if "manifest" in url:
                return Response(
                    200,
                    json={"peer_id": "remote-peer", "snapshot_ids": ["snap-101"]},
                    request=httpx.Request("GET", url),
                )
            else:
                return Response(
                    200,
                    json={
                        "metadata": {
                            "source_id": "src-1",
                            "url": "https://data.example.com",
                            "content_type": "application/json",
                        },
                        "payload": '{"key": "val"}',
                    },
                    request=httpx.Request("GET", url),
                )

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", MockGossipClient)

    # 4. Start & Stop background gossip loop
    node.start()
    assert node._running is True
    await asyncio.sleep(0.05)
    await node.stop()
    assert node._running is False
