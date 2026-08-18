from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from httpx import Response

from continuityos.edge import EdgeManifest, EdgeNode


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_edge_node_mesh_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    node = EdgeNode(node_id="test-edge-node-alpha", cache_dir=tmp_path, gossip_port=18999)

    # 1. Manifest generation
    manifest = node.get_manifest()
    assert manifest.node_id == "test-edge-node-alpha"
    assert manifest.ledger_sequence >= 0

    # 2. Add and prune peers
    node.add_peer("peer-node-1", "127.0.0.1:18998")
    assert "peer-node-1" in node.peers
    assert node.peers["peer-node-1"].is_alive is True

    # 3. Process remote sync request (Ahead, Behind, In Sync)
    # Peer is ahead
    ahead_manifest = EdgeManifest(
        node_id="peer-node-1",
        ledger_sequence=manifest.ledger_sequence + 5,
        head_block_hash="b" * 64,
        active_snapshots={},
        timestamp_unix=manifest.timestamp_unix,
    )
    res_behind = node.process_remote_manifest(ahead_manifest)
    assert res_behind["status"] == "BEHIND"
    assert res_behind["records_needed"] == 5

    # Peer is behind
    behind_manifest = EdgeManifest(
        node_id="peer-node-1",
        ledger_sequence=max(0, manifest.ledger_sequence - 1),
        head_block_hash="c" * 64,
        active_snapshots={},
        timestamp_unix=manifest.timestamp_unix,
    )
    res_ahead = node.process_remote_manifest(behind_manifest)
    assert res_ahead["status"] in {"AHEAD", "IN_SYNC"}

    # Mock HTTP client for gossip loop
    class MockGossipClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url: str, json: dict) -> Response:
            import httpx

            return Response(
                200,
                json={"status": "IN_SYNC", "node_id": "remote-peer"},
                request=httpx.Request("POST", url),
            )

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", MockGossipClient)

    # 4. Start & Stop background gossip loop
    await node.start()
    assert node._running is True
    await asyncio.sleep(0.05)
    await node.stop()
    assert node._running is False
