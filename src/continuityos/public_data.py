from __future__ import annotations

import asyncio
import csv
import io
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Literal
from xml.etree import ElementTree

import httpx

from continuityos.sources.cache import SnapshotCache, SnapshotMetadata


@dataclass(frozen=True, slots=True)
class PublicSourceSpec:
    source_id: str
    name: str
    url: str
    method: Literal["GET", "POST"] = "GET"
    key_env: str | None = None
    key_location: Literal["header", "query"] = "header"
    freshness_hours: float = 24.0
    licence: str = "Verify provider terms before production use"
    parser: Literal["json", "csv", "rss", "geojson"] = "json"


PUBLIC_SOURCE_SPECS: dict[str, PublicSourceSpec] = {
    "eccc-geomet-alerts": PublicSourceSpec(
        "eccc-geomet-alerts",
        "ECCC MSC GeoMet weather alerts",
        "https://api.weather.gc.ca/collections/weather-alerts/items?f=json&limit=100",
        freshness_hours=6.0,
        licence="MSC Datamart End-User Licence / Government of Canada terms",
        parser="geojson",
    ),
    "statcan-wds": PublicSourceSpec(
        "statcan-wds",
        "Statistics Canada WDS cube catalogue",
        "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesListLite",
        freshness_hours=48.0,
        licence="Statistics Canada / Open Government Licence where applicable",
    ),
    "copernicus-cdse-stac": PublicSourceSpec(
        "copernicus-cdse-stac",
        "Copernicus CDSE STAC catalogue",
        "https://stac.dataspace.copernicus.eu/v1/collections",
        freshness_hours=24.0,
        licence="Copernicus free/open data policy and service terms",
    ),
    "usgs-water": PublicSourceSpec(
        "usgs-water",
        "USGS Water Data OGC collections",
        "https://api.waterdata.usgs.gov/ogcapi/v0/collections",
        freshness_hours=24.0,
        licence="USGS public data and API terms",
    ),
    "noaa-swpc": PublicSourceSpec(
        "noaa-swpc",
        "NOAA Space Weather scales",
        "https://services.swpc.noaa.gov/products/noaa-scales.json",
        freshness_hours=6.0,
        licence="NOAA public data",
    ),
    "gdacs": PublicSourceSpec(
        "gdacs",
        "Global Disaster Alert and Coordination System events",
        "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
        freshness_hours=6.0,
        licence="GDACS public API terms",
        parser="geojson",
    ),
    "reliefweb": PublicSourceSpec(
        "reliefweb",
        "UN OCHA ReliefWeb reports",
        "https://api.reliefweb.int/v2/reports?appname={KEY}&limit=10",
        freshness_hours=12.0,
        licence="ReliefWeb API terms; read-only public archive",
        key_env="RELIEFWEB_APPNAME",
        key_location="query",
    ),
    "openalex": PublicSourceSpec(
        "openalex",
        "OpenAlex scholarly metadata",
        "https://api.openalex.org/works?search=critical%20infrastructure&per-page=10",
        freshness_hours=72.0,
        licence="OpenAlex terms and source-level licences",
    ),
    "gdelt": PublicSourceSpec(
        "gdelt",
        "GDELT public event/news context",
        "https://api.gdeltproject.org/api/v2/doc/doc?query=Canada%20Arctic&mode=ArtList&format=json&maxrecords=50",
        freshness_hours=6.0,
        licence="GDELT public access; respect source/news rights and rate limits",
    ),
    "nasa-firms": PublicSourceSpec(
        "nasa-firms",
        "NASA FIRMS active fire data",
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/-141,41,-52,84/1",
        key_env="NASA_FIRMS_MAP_KEY",
        freshness_hours=6.0,
        licence="NASA FIRMS terms; free MAP_KEY required",
        parser="csv",
    ),
}


@dataclass(frozen=True, slots=True)
class PublicSnapshot:
    source_id: str
    snapshot_id: str
    content_sha256: str
    retrieved_at: datetime
    status_code: int
    parser: str
    record_count: int
    freshness_hours: float
    quality_flags: tuple[str, ...]


def _parse_date(value: Any) -> datetime | None:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)
        except ValueError:
            try:
                return parsedate_to_datetime(value).astimezone(UTC)
            except (TypeError, ValueError, OverflowError):
                return None
    return None


def _records(payload: Any, parser: str) -> tuple[int, tuple[str, ...]]:
    flags: list[str] = []
    if parser == "csv":
        if not isinstance(payload, str):
            raise ValueError("CSV parser requires text payload")
        rows = list(csv.DictReader(io.StringIO(payload)))
        if not rows:
            flags.append("empty_dataset")
        return len(rows), tuple(flags)
    if parser == "rss":
        root = ElementTree.fromstring(payload)
        items = root.findall(".//item")
        return len(items), tuple(flags)
    if isinstance(payload, list):
        if not payload:
            flags.append("empty_dataset")
        return len(payload), tuple(flags)
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object or array")
    if parser == "geojson" and payload.get("type") == "FeatureCollection":
        rows = payload.get("features", [])
    elif isinstance(payload.get("features"), list):
        rows = payload["features"]
    elif isinstance(payload.get("data"), list):
        rows = payload["data"]
    elif isinstance(payload.get("items"), list):
        rows = payload["items"]
    elif isinstance(payload.get("results"), list):
        rows = payload["results"]
    elif isinstance(payload.get("collections"), list):
        rows = payload["collections"]
    else:
        rows = [payload]
    if not rows:
        flags.append("empty_dataset")
    return len(rows), tuple(flags)


class PublicDataPlane:
    """Bounded, snapshot-first client for explicitly allow-listed public sources."""

    def __init__(
        self,
        cache: SnapshotCache,
        *,
        outbound_enabled: bool,
        timeout_seconds: float = 20.0,
        max_payload_bytes: int = 10_000_000,
    ) -> None:
        self.cache = cache
        self.outbound_enabled = outbound_enabled
        self.timeout_seconds = timeout_seconds
        self.max_payload_bytes = max_payload_bytes

    async def fetch(self, source_id: str, *, force: bool = False) -> PublicSnapshot:
        try:
            spec = PUBLIC_SOURCE_SPECS[source_id]
        except KeyError as exc:
            raise ValueError(f"source is not allow-listed: {source_id}") from exc
        if not force:
            cached = self.cache.latest(source_id, url=spec.url, max_age_hours=spec.freshness_hours)
            if cached is not None:
                return self._summarize(spec, cached[0], cached[1], from_cache=True)
        if not self.outbound_enabled:
            raise RuntimeError("outbound HTTP disabled; import or use an existing snapshot")
        url = spec.url
        headers = {"User-Agent": "ContinuityOS-Reference/0.1 (+public-data; contact operator)"}
        if spec.key_env:
            key = os.environ.get(spec.key_env, "").strip()
            if not key:
                raise RuntimeError(f"{source_id} requires protected environment key {spec.key_env}")
            if spec.key_location == "header":
                headers["X-Api-Key"] = key
            else:
                url = url.replace("{MAP_KEY}", key).replace("{KEY}", key)
        elif "{MAP_KEY}" in url:
            raise RuntimeError(f"{source_id} requires a protected MAP_KEY")
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response: httpx.Response | None = None
            for attempt in range(3):
                response = await client.get(url, headers=headers)
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                    break
                retry_after = min(float(response.headers.get("retry-after", "1")), 5.0)
                await asyncio.sleep(max(0.1, retry_after))
            assert response is not None
            response.raise_for_status()
            if len(response.content) > self.max_payload_bytes:
                raise ValueError("public source payload exceeds configured size limit")
        metadata = self.cache.store(
            source_id, spec.url, response.content, dict(response.headers), response.status_code
        )
        return self._summarize(spec, metadata, response.content, from_cache=False)

    def summarize_snapshot(
        self, source_id: str, metadata: SnapshotMetadata, body: bytes
    ) -> PublicSnapshot:
        spec = PUBLIC_SOURCE_SPECS[source_id]
        return self._summarize(spec, metadata, body, from_cache=True)

    @staticmethod
    def _summarize(
        spec: PublicSourceSpec,
        metadata: SnapshotMetadata,
        body: bytes,
        *,
        from_cache: bool,
    ) -> PublicSnapshot:
        try:
            if spec.parser == "csv":
                payload: Any = body.decode("utf-8-sig")
            elif spec.parser == "rss":
                payload = body.decode("utf-8", errors="strict")
            else:
                payload = json.loads(body)
            record_count, flags = _records(payload, spec.parser)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ElementTree.ParseError,
            ValueError,
        ) as exc:
            raise ValueError(f"{spec.source_id} payload validation failed: {exc}") from exc
        quality = list(flags)
        if from_cache:
            quality.append("snapshot_cache")
        return PublicSnapshot(
            source_id=spec.source_id,
            snapshot_id=metadata.snapshot_id,
            content_sha256=metadata.content_sha256,
            retrieved_at=datetime.fromisoformat(metadata.retrieved_at).astimezone(UTC),
            status_code=metadata.status_code,
            parser=spec.parser,
            record_count=record_count,
            freshness_hours=spec.freshness_hours,
            quality_flags=tuple(quality),
        )
