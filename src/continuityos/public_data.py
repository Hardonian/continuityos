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
from urllib.parse import urlencode
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
    "dfo-iwls": PublicSourceSpec(
        "dfo-iwls",
        "DFO Canadian Hydrographic Service Integrated Water Level System",
        "https://api-iwls.dfo-mpo.gc.ca/api/v1/",
        freshness_hours=1.0,
        licence="CHS IWLS public web-service licence; QC flags and official tide-table terms apply",
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


@dataclass(frozen=True, slots=True)
class NormalizedIndicator:
    indicator_id: str
    observed_at: datetime
    value: float
    unit: str
    source_id: str
    provenance_snapshot_ids: tuple[str, ...]
    quality_flags: tuple[str, ...]
    metadata: dict[str, str]


class ECCCGeoMetAdapter:
    """Normalize official ECCC alert features without turning alerts into forecasts."""

    @staticmethod
    def normalize_alerts(
        snapshot: PublicSnapshot,
        body: bytes,
        *,
        now: datetime | None = None,
    ) -> list[NormalizedIndicator]:
        payload = json.loads(body)
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise ValueError("ECCC alert response must be a GeoJSON FeatureCollection")
        reference_time = now or datetime.now(UTC)
        indicators: list[NormalizedIndicator] = []
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            props = feature.get("properties")
            if not isinstance(props, dict):
                continue
            observed_at = _parse_date(props.get("publication_datetime")) or snapshot.retrieved_at
            expires = _parse_date(props.get("expiration_datetime"))
            flags: list[str] = []
            if expires is not None and expires < reference_time:
                flags.append("expired_at_normalization")
            confidence = str(props.get("confidence_en") or "unknown").lower()
            if confidence not in {"high", "medium"}:
                flags.append("nonstandard_confidence")
            if feature.get("geometry") is None:
                flags.append("missing_geometry")
            alert_code = str(props.get("alert_code") or "unknown").lower()
            indicators.append(
                NormalizedIndicator(
                    indicator_id=f"eccc.alert.{alert_code}",
                    observed_at=observed_at,
                    value=1.0,
                    unit="active_alert_event",
                    source_id=snapshot.source_id,
                    provenance_snapshot_ids=(snapshot.snapshot_id,),
                    quality_flags=tuple(flags),
                    metadata={
                        "alert_type": str(props.get("alert_type") or "unknown"),
                        "alert_name": str(props.get("alert_name_en") or "unknown"),
                        "province": str(props.get("province") or "unknown"),
                        "status": str(props.get("status_en") or "unknown"),
                        "confidence": confidence,
                        "impact": str(props.get("impact_en") or "unknown"),
                        "expiration_datetime": expires.isoformat() if expires else "",
                    },
                )
            )
        return indicators

    @staticmethod
    async def fetch(
        plane: PublicDataPlane, *, force: bool = False
    ) -> tuple[PublicSnapshot, list[NormalizedIndicator]]:
        snapshot = await plane.fetch("eccc-geomet-alerts", force=force)
        cached = plane.cache.latest(
            "eccc-geomet-alerts",
            url=PUBLIC_SOURCE_SPECS["eccc-geomet-alerts"].url,
            max_age_hours=None,
        )
        if cached is None:
            raise RuntimeError("ECCC snapshot disappeared after fetch")
        return snapshot, ECCCGeoMetAdapter.normalize_alerts(snapshot, cached[1])


class DFOIWLSAdapter:
    """Fetch and normalize CHS IWLS station metadata and water-level observations."""

    @staticmethod
    async def fetch_operating_station(
        plane: PublicDataPlane, *, region: str = "QUE", force: bool = False
    ) -> tuple[PublicSnapshot, dict[str, Any]]:
        if region not in {"ATL", "QUE", "PAC", "CNA"}:
            raise ValueError("DFO region must be ATL, QUE, PAC, or CNA")
        query = urlencode({"chs-region-code": region})
        url = f"https://api-iwls.dfo-mpo.gc.ca/api/v1/stations?{query}"
        snapshot = await plane.fetch_url("dfo-iwls", url, force=force)
        cached = plane.cache.latest("dfo-iwls", url=url, max_age_hours=None)
        if cached is None:
            raise RuntimeError("DFO station snapshot disappeared after fetch")
        payload = json.loads(cached[1])
        if not isinstance(payload, list):
            raise ValueError("DFO station response must be an array")
        for station in payload:
            if not isinstance(station, dict) or not station.get("operating"):
                continue
            series = station.get("timeSeries", [])
            if any(isinstance(item, dict) and item.get("code") == "wlo" for item in series):
                return snapshot, station
        raise ValueError(f"no operating DFO {region} station with wlo series found")

    @staticmethod
    async def fetch_current(
        plane: PublicDataPlane,
        *,
        region: str = "QUE",
        start: datetime,
        end: datetime,
        force: bool = False,
    ) -> tuple[PublicSnapshot, PublicSnapshot, dict[str, Any], list[NormalizedIndicator]]:
        station_snapshot, station = await DFOIWLSAdapter.fetch_operating_station(
            plane, region=region, force=force
        )
        data_snapshot, indicators = await plane.fetch_dfo_water_levels(
            station_id=str(station["id"]), start=start, end=end, force=force
        )
        combined = [
            NormalizedIndicator(
                indicator_id=item.indicator_id,
                observed_at=item.observed_at,
                value=item.value,
                unit=item.unit,
                source_id=item.source_id,
                provenance_snapshot_ids=(
                    station_snapshot.snapshot_id,
                    *item.provenance_snapshot_ids,
                ),
                quality_flags=item.quality_flags,
                metadata={
                    **item.metadata,
                    "station_name": str(station.get("officialName") or "unknown"),
                    "station_code": str(station.get("code") or "unknown"),
                    "latitude": str(station.get("latitude") or ""),
                    "longitude": str(station.get("longitude") or ""),
                },
            )
            for item in indicators
        ]
        return station_snapshot, data_snapshot, station, combined


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
        spec = PUBLIC_SOURCE_SPECS.get(source_id)
        if spec is None:
            raise ValueError(f"source is not allow-listed: {source_id}")
        return await self.fetch_url(source_id, spec.url, force=force)

    async def fetch_url(
        self,
        source_id: str,
        url: str,
        *,
        force: bool = False,
        parser: Literal["json", "csv", "rss", "geojson"] | None = None,
    ) -> PublicSnapshot:
        try:
            spec = PUBLIC_SOURCE_SPECS[source_id]
        except KeyError as exc:
            raise ValueError(f"source is not allow-listed: {source_id}") from exc
        active_parser = parser or spec.parser
        if not force:
            cached = self.cache.latest(source_id, url=url, max_age_hours=spec.freshness_hours)
            if cached is not None:
                return self._summarize(
                    spec, cached[0], cached[1], from_cache=True, parser=active_parser
                )
        if not self.outbound_enabled:
            raise RuntimeError("outbound HTTP disabled; import or use an existing snapshot")
        request_url = url
        headers = {"User-Agent": "ContinuityOS-Reference/0.1 (+public-data; contact operator)"}
        if spec.key_env:
            key = os.environ.get(spec.key_env, "").strip()
            if not key:
                raise RuntimeError(f"{source_id} requires protected environment key {spec.key_env}")
            if spec.key_location == "header":
                headers["X-Api-Key"] = key
            else:
                request_url = request_url.replace("{MAP_KEY}", key).replace("{KEY}", key)
        elif "{MAP_KEY}" in request_url or "{KEY}" in request_url:
            raise RuntimeError(f"{source_id} requires a protected environment value")
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response: httpx.Response | None = None
            for attempt in range(3):
                response = await client.get(request_url, headers=headers)
                if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                    break
                retry_after = min(float(response.headers.get("retry-after", "1")), 5.0)
                await asyncio.sleep(max(0.1, retry_after))
            assert response is not None
            response.raise_for_status()
            if len(response.content) > self.max_payload_bytes:
                raise ValueError("public source payload exceeds configured size limit")
        metadata = self.cache.store(
            source_id, url, response.content, dict(response.headers), response.status_code
        )
        return self._summarize(
            spec, metadata, response.content, from_cache=False, parser=active_parser
        )

    async def fetch_dfo_water_levels(
        self,
        *,
        station_id: str,
        start: datetime,
        end: datetime,
        resolution: str = "SIXTY_MINUTES",
        time_series_code: str = "wlo",
        force: bool = False,
    ) -> tuple[PublicSnapshot, list[NormalizedIndicator]]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("DFO start and end must be timezone-aware")
        if end <= start:
            raise ValueError("DFO end must be after start")
        if resolution not in {
            "ALL",
            "ONE_MINUTE",
            "THREE_MINUTES",
            "FIVE_MINUTES",
            "FIFTEEN_MINUTES",
            "SIXTY_MINUTES",
        }:
            raise ValueError("unsupported DFO IWLS resolution")
        query = urlencode(
            {
                "time-series-code": time_series_code,
                "from": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "to": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "resolution": resolution,
            }
        )
        url = f"https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/{station_id}/data?{query}"
        snapshot = await self.fetch_url("dfo-iwls", url, force=force)
        cached = self.cache.latest("dfo-iwls", url=url, max_age_hours=None)
        if cached is None:
            raise RuntimeError("DFO snapshot disappeared after fetch")
        metadata, body = cached
        payload = json.loads(body)
        if not isinstance(payload, list):
            raise ValueError("DFO data response must be an array")
        indicators: list[NormalizedIndicator] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("DFO data item must be an object")
            observed_at = _parse_date(item.get("eventDate"))
            value = item.get("value")
            if observed_at is None or not isinstance(value, (int, float)):
                continue
            flags = []
            qc = str(item.get("qcFlagCode", "2"))
            if qc != "1":
                flags.append(f"qc_{qc}")
            if item.get("reviewed") is False:
                flags.append("not_reviewed")
            indicators.append(
                NormalizedIndicator(
                    indicator_id="dfo.iwls.water_level",
                    observed_at=observed_at,
                    value=float(value),
                    unit="metres_relative_to_station_product_datum",
                    source_id="dfo-iwls",
                    provenance_snapshot_ids=(metadata.snapshot_id,),
                    quality_flags=tuple(flags),
                    metadata={
                        "station_id": station_id,
                        "time_series_code": time_series_code,
                        "time_series_id": str(item.get("timeSeriesId", "")),
                        "qc_flag_code": qc,
                    },
                )
            )
        if not indicators:
            raise ValueError("DFO response contained no numeric water-level observations")
        return snapshot, indicators

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
        parser: Literal["json", "csv", "rss", "geojson"] | None = None,
    ) -> PublicSnapshot:
        active_parser = parser or spec.parser
        try:
            if active_parser == "csv":
                payload: Any = body.decode("utf-8-sig")
            elif active_parser == "rss":
                payload = body.decode("utf-8", errors="strict")
            else:
                payload = json.loads(body)
            record_count, flags = _records(payload, active_parser)
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
            parser=active_parser,
            record_count=record_count,
            freshness_hours=spec.freshness_hours,
            quality_flags=tuple(quality),
        )
