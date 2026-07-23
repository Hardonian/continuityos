from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import UTC, date, datetime
from statistics import median
from typing import Any

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)


def _provenance(uri: str, body: bytes, snapshot_id: str | None, licence: str) -> Provenance:
    return Provenance(
        uri=uri,
        content_sha256=hashlib.sha256(body).hexdigest(),
        snapshot_id=snapshot_id,
        licence=licence,
    )


def parse_nsidc_daily_extent_csv(
    body: bytes,
    *,
    uri: str,
    snapshot_id: str | None = None,
) -> list[Observation]:
    """Parse NSIDC daily extent and derive 1981-2010 day-of-year anomalies.

    Absolute Arctic-wide extent is climate context, not local navigability. The parser
    therefore derives an anomaly against the Sea Ice Index climatological reference
    period rather than misclassifying absolute extent as route risk. Dates without a
    usable baseline are skipped instead of receiving an invented anomaly.
    """
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)
    parsed: list[tuple[date, float, dict[str, str]]] = []
    for raw in reader:
        row = {str(key).strip().lower(): (value or "").strip() for key, value in raw.items()}
        try:
            extent = float(row.get("extent", row.get("extent_million_sq_km", "")))
            observed = date(int(row["year"]), int(row["month"]), int(row["day"]))
        except (KeyError, TypeError, ValueError):
            continue
        if extent < 0:
            continue
        parsed.append((observed, extent, row))

    baseline: dict[tuple[int, int], list[float]] = {}
    for observed, extent, _row in parsed:
        if 1981 <= observed.year <= 2010:
            baseline.setdefault((observed.month, observed.day), []).append(extent)

    observations: list[Observation] = []
    provenance = _provenance(uri, body, snapshot_id, "NOAA@NSIDC terms")
    for observed, extent, row in parsed:
        values = baseline.get((observed.month, observed.day), [])
        if not values:
            continue
        reference = median(values)
        anomaly = extent - reference
        observations.append(
            Observation(
                source_id="nsidc-sea-ice-index",
                source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
                assertion_class=AssertionClass.CLIMATE,
                metric=MetricName.SEA_ICE_EXTENT_ANOMALY,
                value=round(anomaly, 6),
                unit="million_km2_anomaly",
                observed_at=datetime.combine(observed, datetime.min.time(), tzinfo=UTC),
                confidence=0.97,
                provenance=provenance,
                metadata={
                    "hemisphere": row.get("hemisphere", "north"),
                    "absolute_extent_million_km2": extent,
                    "baseline_median_million_km2": reference,
                    "baseline_period": "1981-2010",
                    "operability_role": "context_only",
                },
            )
        )
    return observations


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_celestrak_gp_json(
    body: bytes,
    *,
    uri: str,
    snapshot_id: str | None = None,
) -> Observation:
    records = json.loads(body)
    if not isinstance(records, list):
        raise ValueError("CelesTrak response must be a JSON array")
    valid: list[dict[str, Any]] = []
    epochs: list[datetime] = []
    for item in records:
        if not isinstance(item, dict) or not item.get("OBJECT_ID"):
            continue
        epoch = _parse_iso_timestamp(item.get("EPOCH"))
        if epoch is None:
            continue
        valid.append(item)
        epochs.append(epoch)
    if not valid:
        raise ValueError("CelesTrak response contains no epoch-qualified GP records")
    return Observation(
        source_id="celestrak-gp",
        source_trust=SourceTrust.OPEN_CONTEXT,
        assertion_class=AssertionClass.ORBITAL_GEOMETRY,
        metric=MetricName.SATELLITE_GEOMETRY_DENSITY,
        value=float(len(valid)),
        unit="catalogued_objects",
        observed_at=max(epochs),
        confidence=0.80,
        provenance=_provenance(uri, body, snapshot_id, "CelesTrak usage policy"),
        metadata={
            "record_count": len(valid),
            "oldest_epoch": min(epochs).isoformat(),
            "latest_epoch": max(epochs).isoformat(),
            "warning": "not service availability",
            "operability_role": "context_only",
        },
    )


def parse_stac_search_response(
    body: bytes,
    *,
    uri: str,
    snapshot_id: str | None = None,
) -> Observation:
    payload: dict[str, Any] = json.loads(body)
    if payload.get("type") != "FeatureCollection":
        raise ValueError("STAC response must be a FeatureCollection")
    features = payload.get("features", [])
    if not isinstance(features, list):
        raise ValueError("STAC features must be an array")
    acquisition_times: list[datetime] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue
        timestamp = _parse_iso_timestamp(
            properties.get("datetime") or properties.get("start_datetime")
        )
        if timestamp is not None:
            acquisition_times.append(timestamp)
    observed_at = max(acquisition_times) if acquisition_times else datetime.now(UTC)
    return Observation(
        source_id="copernicus-cdse-stac",
        source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
        assertion_class=AssertionClass.EARTH_OBSERVATION,
        metric=MetricName.EARTH_OBSERVATION_COVERAGE,
        value=float(len(features)),
        unit="catalogue_features",
        observed_at=observed_at,
        confidence=0.85 if acquisition_times else 0.40,
        provenance=_provenance(uri, body, snapshot_id, "Copernicus data terms"),
        metadata={
            "feature_count": len(features),
            "derived_analysis_required": True,
            "latest_acquisition": (
                max(acquisition_times).isoformat() if acquisition_times else None
            ),
            "operability_role": "context_only",
        },
    )


def build_copernicus_stac_query(
    bbox: tuple[float, float, float, float], start: datetime, end: datetime, limit: int = 100
) -> dict[str, Any]:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("STAC query dates must be timezone-aware")
    if start >= end:
        raise ValueError("start must precede end")
    if not 1 <= limit <= 1000:
        raise ValueError("limit outside supported range")
    west, south, east, north = bbox
    if not (-180.0 <= west < east <= 180.0):
        raise ValueError("invalid STAC longitude bounds")
    if not (-90.0 <= south < north <= 90.0):
        raise ValueError("invalid STAC latitude bounds")
    return {
        "collections": ["sentinel-1-grd"],
        "bbox": list(bbox),
        "datetime": f"{start.isoformat()}/{end.isoformat()}",
        "limit": limit,
    }


def build_celestrak_query(group: str = "starlink") -> str:
    safe = group.strip().lower()
    if not safe.replace("-", "").isalnum():
        raise ValueError("invalid CelesTrak group")
    return f"https://celestrak.org/NORAD/elements/gp.php?GROUP={safe}&FORMAT=JSON"
