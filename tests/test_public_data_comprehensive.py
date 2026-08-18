import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from continuityos.public_data import (
    CanadianDisasterDatabaseAdapter,
    DFOIWLSAdapter,
    ECCCGeoMetAdapter,
    PublicDataPlane,
    PublicSourceSpec,
)
from continuityos.sources.cache import SnapshotCache


@pytest.fixture
def cache(tmp_path):
    return SnapshotCache(tmp_path)


@pytest.fixture
def plane(cache):
    return PublicDataPlane(cache, outbound_enabled=False)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_eccc_geomet_adapter_invalid_json(plane):
    with pytest.raises(ValueError):
        ECCCGeoMetAdapter.normalize_alerts(None, b"invalid")


@pytest.mark.anyio
async def test_eccc_geomet_adapter_invalid_type(plane):
    with pytest.raises(ValueError):
        ECCCGeoMetAdapter.normalize_alerts(None, b'{"type": "Feature"}')


@pytest.mark.anyio
async def test_dfo_iwls_fetch_operating_station_invalid_region(plane):
    with pytest.raises(ValueError):
        await DFOIWLSAdapter.fetch_operating_station(plane, region="INVALID")


@pytest.mark.anyio
async def test_dfo_iwls_fetch_operating_station_not_found(plane):
    plane.fetch_url = AsyncMock(return_value=None)
    plane.cache.latest = lambda *args, **kwargs: (None, b'[]')
    with pytest.raises(ValueError):
        await DFOIWLSAdapter.fetch_operating_station(plane, region="QUE")


@pytest.mark.anyio
async def test_dfo_iwls_fetch_current_invalid_dates(plane):
    with pytest.raises(ValueError):
        await plane.fetch_dfo_water_levels(station_id="1", start=datetime.now(), end=datetime.now())


@pytest.mark.anyio
async def test_fetch_dfo_water_levels_invalid_resolution(plane):
    with pytest.raises(ValueError):
        await plane.fetch_dfo_water_levels(station_id="1", start=datetime.now(UTC), end=datetime.now(UTC), resolution="INVALID")


@pytest.mark.anyio
async def test_fetch_dfo_water_levels_invalid_response(plane):
    from unittest.mock import MagicMock
    plane.fetch_url = AsyncMock(return_value=None)
    plane.cache.latest = lambda *args, **kwargs: (MagicMock(), b'{}')
    with pytest.raises(ValueError):
        await plane.fetch_dfo_water_levels(station_id="1", start=datetime.now(UTC), end=datetime.now(UTC))

