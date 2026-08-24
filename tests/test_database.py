"""Test suite for Transactional Indexed Evidence Database."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.database import TransactionalEvidenceStore
from continuityos.service import create_app


class TestTransactionalEvidenceStore:
    """Test indexed SQLite storage and queries."""

    def test_insert_and_query(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        rec = store.insert_record(
            tenant_id="TENANT-HQ",
            corridor_id="CORR-ARCTIC",
            sequence_num=1,
            payload_type="RADAR_OBSERVATION",
            payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            payload={"status": "NOMINAL", "track_count": 14},
        )

        assert rec.sequence_num == 1
        assert store.count_records("TENANT-HQ") == 1
        assert store.count_records("TENANT-OTHER") == 0

        queried = store.query_records(tenant_id="TENANT-HQ", corridor_id="CORR-ARCTIC")
        assert len(queried) == 1
        assert queried[0]["payload"]["track_count"] == 14

        store.close()


class TestDatabaseAPI:
    """Test database query REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_database_query_endpoint(self, client: TestClient) -> None:
        resp = client.get("/v1/database/evidence/query?tenant_id=DND-CARLING-HQ")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_count" in data
        assert "records" in data
