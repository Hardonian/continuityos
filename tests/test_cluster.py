"""Test suite for Air-Gapped DDIL SCIF Cluster & Raft State Synchronization."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.cluster import ClusterNodeRole, RaftStateSynchronizer
from continuityos.service import create_app


class TestRaftStateSynchronizer:
    """Test distributed consensus and log replication in air-gapped SCIF mesh."""

    def test_append_command_and_merkle_root(self) -> None:
        cluster = RaftStateSynchronizer("SCIF-OTTAWA", "DND-Carling-SCIF")
        entry = cluster.append_command("SEALED_INTEL", {"threat": "HIGH", "target": "NORTH_BAY"})

        assert entry.index == 1
        assert entry.term == 1
        assert len(cluster.log) == 1
        root = cluster.compute_merkle_root()
        assert len(root) == 64  # SHA-256 hex string

    def test_peer_registration_and_sync(self) -> None:
        cluster = RaftStateSynchronizer("SCIF-OTTAWA", "DND-Carling-SCIF")
        cluster.register_peer("SCIF-HALIFAX", "CFB-Halifax-SCIF", True, 512.0)

        cluster.append_command("EMCON_DIRECTIVE", {"posture": "ALPHA_SILENT"})
        cluster.append_command("RADAR_ALERT", {"status": "ANOMALY"})

        sync_res = cluster.sync_with_peer("SCIF-HALIFAX", peer_log_index=0)
        assert sync_res.entries_replicated == 2
        assert sync_res.sync_status == "SYNCHRONIZED_NOMINAL"
        assert cluster.peers["SCIF-HALIFAX"].role == ClusterNodeRole.FOLLOWER


class TestClusterAPI:
    """Test cluster REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_cluster_status_endpoint(self, client: TestClient) -> None:
        resp = client.get("/v1/cluster/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "local_node_id" in data
        assert "merkle_state_root" in data

    def test_cluster_peer_sync_endpoint(self, client: TestClient) -> None:
        payload = {"peer_id": "SCIF-NODE-HALIFAX", "last_log_index": 0}
        resp = client.post("/v1/cluster/peers/sync", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sync_status"] == "SYNCHRONIZED_NOMINAL"
