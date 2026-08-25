"""Extended unit tests for Public Data Plane adapters & normalization.

Targets: public_data.py coverage from 78% → ≥95%.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

import pytest

from continuityos.public_data import (
    CanadianDisasterDatabaseAdapter,
    DFOIWLSAdapter,
    ECCCGeoMetAdapter,
    PublicDataPlane,
    PublicSnapshot,
    _parse_date,
    _parse_excel_date,
    _xlsx_rows,
)
from continuityos.sources.cache import SnapshotCache

pytestmark = pytest.mark.anyio


def test_xlsx_rows_no_sheet1() -> None:
    """XLSX without sheet1.xml raises ValueError."""
    buf = io.BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", "<workbook/>")

    with pytest.raises(ValueError, match="no first worksheet"):
        _xlsx_rows(buf.getvalue())


def test_xlsx_rows_empty_workbook() -> None:
    """XLSX with empty sheet returns empty list."""
    buf = io.BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )

    rows = _xlsx_rows(buf.getvalue())
    assert rows == []


def test_parse_excel_date() -> None:
    """Test Excel float dates, string dates, and invalid/null dates."""
    assert _parse_excel_date(None) is None
    assert _parse_excel_date("") is None
    assert _parse_excel_date("NULL") is None

    # Excel serial day 45000 is ~2023-03-15
    parsed = _parse_excel_date("45000")
    assert parsed is not None
    assert parsed.year == 2023

    # Fallback to standard ISO string
    iso_parsed = _parse_excel_date("2024-06-01T12:00:00Z")
    assert iso_parsed is not None
    assert iso_parsed.year == 2024


def test_parse_date_rfc_fallback() -> None:
    """RFC-style HTTP date parsing fallback."""
    parsed = _parse_date("Wed, 21 Oct 2015 07:28:00 GMT")
    assert parsed is not None
    assert parsed.year == 2015

    assert _parse_date("not-a-date-at-all") is None
    assert _parse_date(12345) is None


def test_cdd_adapter_no_dated_events_raises(tmp_path: Path) -> None:
    """CDD workbook with headers but no dated rows raises ValueError."""
    cache = SnapshotCache(tmp_path)

    # Minimal sheet with only headers
    buf = io.BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                <sheetData>
                    <row r="1">
                        <c r="A1" t="inlineStr"><is><t>EVENT_ID</t></is></c>
                        <c r="B1" t="inlineStr"><is><t>EVENT_START_DATE</t></is></c>
                    </row>
                </sheetData>
            </worksheet>""",
        )

    cache.store("canadian-disaster-database", "https://example.com", buf.getvalue(), {}, 200)

    mock_snap = PublicSnapshot(
        source_id="canadian-disaster-database",
        snapshot_id="snap-1",
        content_sha256="a" * 64,
        retrieved_at=datetime.now(UTC),
        status_code=200,
        parser="xlsx",
        record_count=0,
        freshness_hours=720.0,
        quality_flags=(),
    )
    with pytest.raises(ValueError, match="contained no dated event rows"):
        CanadianDisasterDatabaseAdapter.normalize_events(mock_snap, buf.getvalue())


def test_eccc_alert_nonstandard_confidence() -> None:
    """ECCC alert with low or unknown confidence gets nonstandard_confidence flag."""
    mock_snap = PublicSnapshot(
        source_id="eccc-geomet-alerts",
        snapshot_id="snap-1",
        content_sha256="a" * 64,
        retrieved_at=datetime.now(UTC),
        status_code=200,
        parser="geojson",
        record_count=1,
        freshness_hours=6.0,
        quality_flags=(),
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "alert_code": "wind_warning",
                    "confidence_en": "low",  # nonstandard
                    "publication_datetime": "2024-01-01T00:00:00Z",
                    "expiration_datetime": "2020-01-01T00:00:00Z",  # expired
                },
                "geometry": None,  # missing geometry
            },
            "non-dict-feature",  # skipped
            {"type": "Feature", "properties": "not-dict"},  # skipped
        ],
    }

    body = json.dumps(feature_collection).encode()
    indicators = ECCCGeoMetAdapter.normalize_alerts(mock_snap, body)

    assert len(indicators) == 1
    flags = indicators[0].quality_flags
    assert "expired_at_normalization" in flags
    assert "nonstandard_confidence" in flags
    assert "missing_geometry" in flags


async def test_fetch_url_payload_size_limit_exceeded(tmp_path: Path) -> None:
    """When downloaded payload exceeds max_payload_bytes, raise ValueError."""
    cache = SnapshotCache(tmp_path)
    plane = PublicDataPlane(cache, outbound_enabled=True, max_payload_bytes=10)

    mock_resp = AsyncMock()
    mock_resp.content = b"a" * 100  # 100 bytes > 10 max
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = AsyncMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("httpx.AsyncClient", return_value=mock_client),
        pytest.raises(ValueError, match="exceeds configured size limit"),
    ):
        await plane.fetch_url(
            "eccc-geomet-alerts",
            "https://api.weather.gc.ca/collections/weather-alerts/items?f=json&limit=100",
            force=True,
        )


async def test_fetch_dfo_station_and_water_levels_combined(tmp_path: Path) -> None:
    """DFOIWLSAdapter.fetch_current coordinates station & level fetches."""
    cache = SnapshotCache(tmp_path)
    plane = PublicDataPlane(cache, outbound_enabled=False)

    station_data = [
        {
            "id": "STN-001",
            "officialName": "Halifax Tide Gauge",
            "code": "HLX",
            "latitude": 44.65,
            "longitude": -63.58,
            "operating": True,
            "timeSeries": [{"code": "wlo"}],
        }
    ]
    water_levels_data = [
        {"eventDate": "2024-01-01T00:00:00Z", "value": 1.45, "qcFlagCode": "1"},
        {"eventDate": "2024-01-01T01:00:00Z", "value": 1.55, "qcFlagCode": "1"},
    ]

    # Pre-populate cache
    cache.store(
        "dfo-iwls",
        "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations?chs-region-code=ATL",
        json.dumps(station_data).encode(),
        {"content-type": "application/json"},
        200,
    )
    cache.store(
        "dfo-iwls",
        "https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/STN-001/data?time-series-code=wlo&from=2024-01-01T00%3A00%3A00Z&to=2024-01-02T00%3A00%3A00Z&resolution=SIXTY_MINUTES",
        json.dumps(water_levels_data).encode(),
        {"content-type": "application/json"},
        200,
    )

    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 2, tzinfo=UTC)

    (
        _stn_snap,
        _data_snap,
        station,
        indicators,
    ) = await DFOIWLSAdapter.fetch_current(
        plane,
        region="ATL",
        start=start,
        end=end,
    )

    assert station["id"] == "STN-001"
    assert len(indicators) == 2
    assert indicators[0].metadata["station_code"] == "HLX"
