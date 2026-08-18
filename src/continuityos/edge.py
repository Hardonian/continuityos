from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel

from continuityos.sources.cache import SnapshotCache

logger = logging.getLogger("continuityos.edge")


class EdgeManifest(BaseModel):
    """Manifest of snapshot hashes hosted by a peer."""

    peer_id: str
    snapshot_ids: list[str]


class EdgeNode:
    """
    P2P Gossip Cache protocol node for Sovereign Air-Gapped environments.
    Synchronizes PublicSnapshots between disconnected nodes without central infrastructure.
    """

    def __init__(
        self,
        node_id: str,
        cache: SnapshotCache,
        gossip_interval: float = 30.0,
    ) -> None:
        self.node_id = node_id
        self.cache = cache
        self.gossip_interval = gossip_interval
        self.peers: set[str] = set()
        self._running = False
        self._task: asyncio.Task[Any] | None = None

    def add_peer(self, url: str) -> None:
        """Add a peer URL to the local gossip ring."""
        self.peers.add(url.rstrip("/"))
        logger.info(f"Edge Node {self.node_id} added peer: {url}")

    def get_manifest(self) -> EdgeManifest:
        """Generate a manifest of all local snapshot IDs."""
        snapshot_ids = []
        for metadata_path in self.cache.root.glob("*/*/*/metadata.json"):
            import json

            try:
                data = json.loads(metadata_path.read_text())
                snapshot_ids.append(data["snapshot_id"])
            except (json.JSONDecodeError, KeyError):
                continue
        return EdgeManifest(peer_id=self.node_id, snapshot_ids=snapshot_ids)

    async def _sync_with_peer(self, peer_url: str) -> None:
        """Sync missing snapshots from a single peer."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{peer_url}/v1/edge/manifest")
                if resp.status_code != 200:
                    return

                manifest = EdgeManifest.model_validate(resp.json())
                local_manifest = self.get_manifest()
                local_ids = set(local_manifest.snapshot_ids)

                missing_ids = set(manifest.snapshot_ids) - local_ids

                for missing_id in missing_ids:
                    # Request the raw snapshot payload
                    sync_resp = await client.get(f"{peer_url}/v1/edge/sync/{missing_id}")
                    if sync_resp.status_code == 200:
                        # Extract the metadata from the response headers or body
                        # For simplicity in this reference architecture, we treat the sync
                        # response as a JSON dictionary containing 'metadata' and 'payload'
                        # Alternatively, we could just rely on the standard import_file mechanism.
                        data = sync_resp.json()
                        source_id = data["metadata"]["source_id"]
                        url = data["metadata"]["url"]
                        body = (
                            data["payload"].encode()
                            if isinstance(data["payload"], str)
                            else bytes.fromhex(data["payload"])
                        )
                        headers = {"content-type": data["metadata"].get("content_type") or ""}

                        self.cache.store(source_id, url, body, headers, 200)
                        logger.info(
                            f"Edge Node {self.node_id} synced snapshot {missing_id} from {peer_url}"
                        )

        except (httpx.RequestError, ValueError) as e:
            logger.warning(f"Edge Node {self.node_id} failed to sync with {peer_url}: {e}")

    async def _loop(self) -> None:
        """Background asynchronous gossip loop."""
        logger.info(
            f"Edge Node {self.node_id} starting gossip loop (interval={self.gossip_interval}s)"
        )
        while self._running:
            for peer in list(self.peers):
                await self._sync_with_peer(peer)
            await asyncio.sleep(self.gossip_interval)

    def start(self) -> None:
        """Start the background gossip loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the background gossip loop."""
        import contextlib

        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
