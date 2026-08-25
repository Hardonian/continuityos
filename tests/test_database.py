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

    def test_context_manager(self) -> None:
        """Context manager properly closes connection."""
        with TransactionalEvidenceStore(":memory:") as store:
            store.insert_record(
                tenant_id="T1",
                corridor_id="C1",
                sequence_num=1,
                payload_type="TEST",
                payload_hash="a" * 64,
                payload={"ok": True},
            )
            assert store.count_records("T1") == 1
        # After exit, store should be closed
        assert store._closed is True

    def test_double_close_safe(self) -> None:
        """Closing twice does not raise."""
        store = TransactionalEvidenceStore(":memory:")
        store.close()
        store.close()  # Should not raise

    def test_insert_empty_tenant_id_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="tenant_id must be a non-empty"):
            store.insert_record(
                tenant_id="",
                corridor_id="C1",
                sequence_num=1,
                payload_type="TEST",
                payload_hash="a" * 64,
                payload={},
            )
        store.close()

    def test_insert_empty_corridor_id_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="corridor_id must be a non-empty"):
            store.insert_record(
                tenant_id="T1",
                corridor_id="",
                sequence_num=1,
                payload_type="TEST",
                payload_hash="a" * 64,
                payload={},
            )
        store.close()

    def test_query_limit_too_high_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="limit must be between"):
            store.query_records(tenant_id="T1", limit=5000)
        store.close()

    def test_query_limit_zero_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="limit must be between"):
            store.query_records(tenant_id="T1", limit=0)
        store.close()

    def test_query_negative_offset_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="offset must be between"):
            store.query_records(tenant_id="T1", offset=-1)
        store.close()

    def test_query_empty_tenant_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="tenant_id must be a non-empty"):
            store.query_records(tenant_id="")
        store.close()

    def test_query_empty_corridor_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="corridor_id must be non-empty when provided"):
            store.query_records(tenant_id="T1", corridor_id="")
        store.close()

    def test_count_empty_tenant_rejected(self) -> None:
        store = TransactionalEvidenceStore(":memory:")
        with pytest.raises(ValueError, match="tenant_id must be a non-empty"):
            store.count_records("")
        store.close()

    def test_query_none_corridor_skips_filter(self) -> None:
        """corridor_id=None should return all records for the tenant."""
        store = TransactionalEvidenceStore(":memory:")
        store.insert_record(
            tenant_id="T1",
            corridor_id="C1",
            sequence_num=1,
            payload_type="A",
            payload_hash="a" * 64,
            payload={},
        )
        store.insert_record(
            tenant_id="T1",
            corridor_id="C2",
            sequence_num=2,
            payload_type="B",
            payload_hash="b" * 64,
            payload={},
        )
        results = store.query_records(tenant_id="T1", corridor_id=None)
        assert len(results) == 2
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
