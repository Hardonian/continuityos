from __future__ import annotations

import json
import sqlite3
import struct
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from continuityos.evidence import EvidenceRecord


class ExchangeManifest(BaseModel):
    schema_version: str = "continuityos.evidence-export.v1"
    generated_at: datetime
    record_count: int = Field(ge=0)
    first_record_at: str | None = None
    last_record_at: str | None = None
    record_hashes: list[str]
    content_sha256: str
    source: str = "continuityos://evidence-ledger"
    limitations: list[str]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: dict[str, Any] | None
    properties: dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
    numberMatched: int
    numberReturned: int
    timeStamp: datetime
    links: list[dict[str, str]]


def _coordinates(payload: dict[str, Any]) -> tuple[float, float] | None:
    candidates: list[Any] = [payload, payload.get("metadata")]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        latitude = candidate.get("latitude", candidate.get("lat"))
        longitude = candidate.get("longitude", candidate.get("lon", candidate.get("lng")))
        if (
            isinstance(latitude, (int, float))
            and isinstance(longitude, (int, float))
            and -90 <= float(latitude) <= 90
            and -180 <= float(longitude) <= 180
        ):
            return float(longitude), float(latitude)
    return None


def feature_from_record(record: EvidenceRecord) -> GeoJSONFeature:
    properties: dict[str, Any] = {
        "record_id": record.record_id,
        "record_type": record.record_type,
        "subject_id": record.subject_id,
        "created_at": record.created_at,
        "record_hash": record.record_hash,
        "previous_hash": record.previous_hash,
        "signed": record.signature is not None,
        "payload": record.payload,
    }
    coordinates = _coordinates(record.payload)
    geometry = {"type": "Point", "coordinates": coordinates} if coordinates else None
    return GeoJSONFeature(id=record.record_id, geometry=geometry, properties=properties)


def feature_collection(
    records: list[EvidenceRecord], base_url: str = "/v1/ogc/collections/evidence/items"
) -> GeoJSONFeatureCollection:
    features = [feature_from_record(record) for record in records]
    return GeoJSONFeatureCollection(
        features=features,
        numberMatched=len(features),
        numberReturned=len(features),
        timeStamp=datetime.now(UTC),
        links=[{"rel": "self", "href": base_url, "type": "application/geo+json"}],
    )


def export_manifest(records: list[EvidenceRecord]) -> ExchangeManifest:
    serialized = json.dumps(
        [record.model_dump(mode="json") for record in records],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    import hashlib

    created = [record.created_at for record in records]
    return ExchangeManifest(
        generated_at=datetime.now(UTC),
        record_count=len(records),
        first_record_at=min(created) if created else None,
        last_record_at=max(created) if created else None,
        record_hashes=[record.record_hash for record in records],
        content_sha256=hashlib.sha256(serialized).hexdigest(),
        limitations=[
            "Export is a read-only evidence snapshot, not a live feed.",
            "Geometry is present only when the source payload contains valid "
            "latitude/longitude fields.",
            "No standards conformance certification or customer-system connectivity is implied.",
        ],
    )


def ndjson_bytes(records: list[EvidenceRecord]) -> bytes:
    """Create deterministic newline-delimited JSON for lake/SIEM staging."""
    return b"".join(record.model_dump_json().encode("utf-8") + b"\n" for record in records)


def geopackage_bytes(records: list[EvidenceRecord]) -> bytes:
    """Create a minimal GeoPackage 1.3-compatible SQLite snapshot in memory."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            """
            PRAGMA application_id = 1196444487;
            PRAGMA user_version = 10300;
            CREATE TABLE gpkg_spatial_ref_sys (
                srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
                organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
                definition TEXT NOT NULL, description TEXT
            );
            INSERT INTO gpkg_spatial_ref_sys VALUES
              ('WGS 84 geodetic', 4326, 'EPSG', 4326,
               'WGS 84', NULL);
            CREATE TABLE gpkg_contents (
                table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
                identifier TEXT UNIQUE, description TEXT DEFAULT '', last_change DATETIME NOT NULL,
                min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER
            );
            CREATE TABLE gpkg_geometry_columns (
                table_name TEXT NOT NULL, column_name TEXT NOT NULL,
                geometry_type_name TEXT NOT NULL,
                srs_id INTEGER NOT NULL, z TINYINT NOT NULL, m TINYINT NOT NULL,
                PRIMARY KEY (table_name, column_name)
            );
            CREATE TABLE evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT NOT NULL UNIQUE,
                record_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                properties TEXT NOT NULL,
                geom BLOB
            );
            """
        )
        now = datetime.now(UTC).isoformat()
        connection.execute(
            "INSERT INTO gpkg_contents VALUES "
            "(?, 'features', ?, ?, ?, NULL, NULL, NULL, NULL, 4326)",
            ("evidence", "ContinuityOS evidence", "Read-only evidence snapshot", now),
        )
        connection.execute(
            "INSERT INTO gpkg_geometry_columns VALUES ('evidence', 'geom', 'POINT', 4326, 0, 0)"
        )
        for record in records:
            coordinates = _coordinates(record.payload)
            geom: bytes | None = None
            if coordinates:
                x, y = coordinates
                wkb = b"\x01" + struct.pack("<I", 1) + struct.pack("<dd", x, y)
                geom = b"GP" + bytes((0, 1)) + struct.pack("<i", 4326) + wkb
            feature = feature_from_record(record)
            connection.execute(
                "INSERT INTO evidence "
                "(record_id, record_type, subject_id, created_at, record_hash, properties, geom) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.record_type,
                    record.subject_id,
                    record.created_at,
                    record.record_hash,
                    json.dumps(feature.properties, sort_keys=True, separators=(",", ":")),
                    geom,
                ),
            )
        connection.commit()
        return connection.serialize()
    finally:
        connection.close()
