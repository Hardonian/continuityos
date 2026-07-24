from __future__ import annotations

import asyncio
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from zipfile import ZipFile

from continuityos.public_data import (
    CanadianDisasterDatabaseAdapter,
    DFOIWLSAdapter,
    ECCCGeoMetAdapter,
    PublicDataPlane,
    PublicSnapshot,
    _parse_excel_date,
    _records,
    _xlsx_rows,
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


def test_cdd_xlsx_normalizer_marks_secondary_historical_context() -> None:
    def cell(reference: str, value: str) -> str:
        return f'<c r="{reference}" t="inlineStr"><is><t>{value}</t></is></c>'

    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        f'<row r="1">{cell("A1", "EVENT_ID")}'
        f"{cell('B1', 'EVENT_START_DATE')}{cell('C1', 'DEAD')}</row>"
        f'<row r="2">{cell("A2", "42")}{cell("B2", "36526")}{cell("C2", "3")}</row>'
        "</sheetData></worksheet>"
    ).encode()
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    indicators = CanadianDisasterDatabaseAdapter.normalize_events(
        snapshot("canadian-disaster-database"), output.getvalue()
    )
    assert {item.indicator_id for item in indicators} == {
        "cdd.disaster_event",
        "cdd.deaths",
    }
    assert all("not_primary_source" in item.quality_flags for item in indicators)
    death = next(item for item in indicators if item.indicator_id == "cdd.deaths")
    assert death.value == 3.0
    assert death.observed_at.isoformat() == "2000-01-01T00:00:00+00:00"


def test_xlsx_shared_strings_and_empty_records_are_supported() -> None:
    sheet = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        b'<row r="1"><c r="A1" t="s"><v>0</v></c></row>'
        b'<row r="2"><c r="A2" t="s"><v>1</v></c></row>'
        b"</sheetData></worksheet>"
    )
    shared = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        b"<si><t>header</t></si><si><t>value</t></si></sst>"
    )
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    assert _xlsx_rows(output.getvalue()) == [{"header": "value"}]
    assert _records(output.getvalue(), "xlsx")[0] == 1
    empty = io.BytesIO()
    with ZipFile(empty, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                "<sheetData /></worksheet>"
            ),
        )
    assert _records(empty.getvalue(), "xlsx") == (0, ("empty_dataset",))


def test_excel_date_parser_handles_missing_and_iso_values() -> None:
    assert _parse_excel_date("") is None
    parsed = _parse_excel_date("2026-07-23T00:00:00Z")
    assert parsed is not None
    assert parsed.year == 2026
