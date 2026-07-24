from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from continuityos.domain import AssertionClass, MetricName, Observation, Provenance, SourceTrust
from continuityos.evidence import EvidenceLedger
from continuityos.exchange import export_manifest, feature_collection, geopackage_bytes


def _observation() -> Observation:
    return Observation(
        source_id="operator-telemetry",
        source_trust=SourceTrust.AUTHENTICATED_OPERATOR,
        assertion_class=AssertionClass.CYBER_HEALTH,
        metric=MetricName.CYBER_CONTROL_HEALTH,
        value=0.9,
        unit="ratio",
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
        confidence=0.95,
        provenance=Provenance(
            uri="fixture://exchange",
            content_sha256="a" * 64,
            licence="test",
        ),
        metadata={"latitude": 47.4, "longitude": -70.3},
    )


def test_exchange_exports_are_hashed_and_geospatial(tmp_path) -> None:
    ledger = EvidenceLedger(tmp_path / "ledger.jsonl")
    record = ledger.append("observation", "asset-a", _observation().model_dump(mode="json"))
    records = ledger.records()

    collection = feature_collection(records)
    assert collection.numberMatched == 1
    assert collection.features[0].geometry == {"type": "Point", "coordinates": (-70.3, 47.4)}
    manifest = export_manifest(records)
    assert manifest.record_hashes == [record.record_hash]
    assert len(manifest.content_sha256) == 64

    package = geopackage_bytes(records)
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(package)
        assert (
            connection.execute("SELECT application_id FROM pragma_application_id").fetchone()[0]
            == 1196444487
        )
        row = connection.execute("SELECT record_id, geom FROM evidence").fetchone()
        assert row[0] == record.record_id
        assert row[1].startswith(b"GP")
    finally:
        connection.close()


def test_exchange_empty_snapshot_is_valid(tmp_path) -> None:
    ledger = EvidenceLedger(tmp_path / "ledger.jsonl")
    assert export_manifest(ledger.records()).record_count == 0
    assert feature_collection(ledger.records()).features == []
