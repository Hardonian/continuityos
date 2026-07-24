from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from continuityos.public_data import (
    DFOIWLSAdapter,
    ECCCGeoMetAdapter,
    PublicDataPlane,
    PublicSnapshot,
)
from continuityos.sources.cache import SnapshotCache


def snapshot(source_id: str = "eccc-geomet-alerts") -> PublicSnapshot:
    return PublicSnapshot(
        source_id=source_id,
        snapshot_id=f"{source_id}-snapshot",
        content_sha256="a" * 64,
        retrieved_at=datetime(2026, 7, 23, tzinfo=UTC),
        status_code=200,
        parser="geojson",
        record_count=1,
        freshness_hours=6.0,
        quality_flags=(),
    )


def test_eccc_alerts_normalize_with_quality_and_provenance() -> None:
    body = json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "alert_code": "EHW",
                        "alert_type": "warning",
                        "alert_name_en": "heat warning",
                        "publication_datetime": "2026-07-23T00:00:00Z",
                        "expiration_datetime": "2026-07-23T01:00:00Z",
                        "confidence_en": "High",
                        "impact_en": "Moderate",
                        "province": "QC",
                    },
                }
            ],
        }
    ).encode()
    indicators = ECCCGeoMetAdapter.normalize_alerts(
        snapshot(), body, now=datetime(2026, 7, 23, 2, tzinfo=UTC)
    )
    assert len(indicators) == 1
    item = indicators[0]
    assert item.indicator_id == "eccc.alert.ehw"
    assert item.value == 1.0
    assert item.provenance_snapshot_ids == ("eccc-geomet-alerts-snapshot",)
    assert set(item.quality_flags) == {"expired_at_normalization", "missing_geometry"}
    assert item.metadata["province"] == "QC"


def test_dfo_water_level_normalize_preserves_qc_and_snapshot(tmp_path: Path) -> None:
    cache = SnapshotCache(tmp_path)
    plane = PublicDataPlane(cache, outbound_enabled=False)
    start = datetime(2026, 7, 23, 0, tzinfo=UTC)
    end = datetime(2026, 7, 23, 1, tzinfo=UTC)
    query = urlencode(
        {
            "time-series-code": "wlo",
            "from": "2026-07-23T00:00:00Z",
            "to": "2026-07-23T01:00:00Z",
            "resolution": "SIXTY_MINUTES",
        }
    )
    url = f"https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/station/data?{query}"
    payload = [
        {
            "eventDate": "2026-07-23T00:00:00Z",
            "qcFlagCode": "1",
            "reviewed": True,
            "timeSeriesId": "series",
            "value": 3.229,
        },
        {
            "eventDate": "2026-07-23T01:00:00Z",
            "qcFlagCode": "3",
            "reviewed": False,
            "timeSeriesId": "series",
            "value": 3.932,
        },
    ]
    path = tmp_path / "dfo.json"
    path.write_text(json.dumps(payload))
    cache.import_file("dfo-iwls", url, path)
    _snapshot, indicators = asyncio.run(
        plane.fetch_dfo_water_levels(station_id="station", start=start, end=end)
    )
    assert [item.value for item in indicators] == [3.229, 3.932]
    assert indicators[0].provenance_snapshot_ids[0].startswith("dfo-iwls-")
    assert indicators[0].quality_flags == ()
    assert set(indicators[1].quality_flags) == {"qc_3", "not_reviewed"}


def test_dfo_station_selector_requires_operating_wlo_station(tmp_path: Path) -> None:
    cache = SnapshotCache(tmp_path)
    plane = PublicDataPlane(cache, outbound_enabled=False)
    url = "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations?chs-region-code=QUE"
    path = tmp_path / "stations.json"
    path.write_text(
        json.dumps(
            [
                {"id": "offline", "operating": False, "timeSeries": [{"code": "wlo"}]},
                {
                    "id": "live",
                    "code": "123",
                    "officialName": "Test Station",
                    "operating": True,
                    "timeSeries": [{"code": "wlo"}],
                },
            ]
        )
    )
    cache.import_file("dfo-iwls", url, path)
    _metadata, station = asyncio.run(DFOIWLSAdapter.fetch_operating_station(plane))
    assert station["id"] == "live"
