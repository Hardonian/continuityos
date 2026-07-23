from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx

from continuityos.domain import Observation
from continuityos.sources.adapters import (
    build_celestrak_query,
    build_copernicus_stac_query,
    parse_celestrak_gp_json,
    parse_nsidc_daily_extent_csv,
    parse_stac_search_response,
)
from continuityos.sources.cache import SnapshotCache, SnapshotMetadata

NSIDC_NORTH_DAILY_EXTENT = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv"
)
COPERNICUS_STAC_SEARCH = "https://stac.dataspace.copernicus.eu/v1/search"


class OpenSourceIngestor:
    """Bounded snapshot-first ingestion for selected authoritative open sources.

    Fresh matching snapshots are used before any network request. Outbound access is
    denied unless enabled. Every network response is stored content-addressably before
    parsing so assessments can be reproduced offline.
    """

    def __init__(
        self,
        cache: SnapshotCache,
        *,
        outbound_enabled: bool,
        timeout_seconds: float = 20.0,
        max_cache_age_hours: float = 24.0,
    ) -> None:
        self.cache = cache
        self.outbound_enabled = outbound_enabled
        self.timeout_seconds = timeout_seconds
        self.max_cache_age_hours = max_cache_age_hours

    async def _get_or_fetch(self, source_id: str, url: str) -> tuple[SnapshotMetadata, bytes]:
        cached = self.cache.latest(
            source_id,
            url=url,
            max_age_hours=self.max_cache_age_hours,
        )
        if cached is not None:
            return cached
        return await self.cache.fetch(
            source_id,
            url,
            outbound_enabled=self.outbound_enabled,
        )

    async def nsidc_daily_extent(self) -> list[Observation]:
        metadata, body = await self._get_or_fetch(
            "nsidc-sea-ice-index",
            NSIDC_NORTH_DAILY_EXTENT,
        )
        return parse_nsidc_daily_extent_csv(
            body,
            uri=NSIDC_NORTH_DAILY_EXTENT,
            snapshot_id=metadata.snapshot_id,
        )

    async def celestrak_geometry(self, group: str = "starlink") -> Observation:
        url = build_celestrak_query(group)
        metadata, body = await self._get_or_fetch("celestrak-gp", url)
        return parse_celestrak_gp_json(body, uri=url, snapshot_id=metadata.snapshot_id)

    async def copernicus_stac(
        self,
        bbox: tuple[float, float, float, float],
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> Observation:
        query = build_copernicus_stac_query(bbox, start, end, limit)
        canonical_request = json.dumps(query, sort_keys=True, separators=(",", ":"))
        source_uri = f"{COPERNICUS_STAC_SEARCH}#request={canonical_request}"
        cached = self.cache.latest(
            "copernicus-cdse-stac",
            url=source_uri,
            max_age_hours=self.max_cache_age_hours,
        )
        if cached is not None:
            metadata, body = cached
            return parse_stac_search_response(
                body,
                uri=source_uri,
                snapshot_id=metadata.snapshot_id,
            )
        if not self.outbound_enabled:
            raise RuntimeError("outbound HTTP disabled; import a saved STAC response instead")
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.post(
                COPERNICUS_STAC_SEARCH,
                json=query,
                headers={"User-Agent": "ContinuityOS-Reference/0.1"},
            )
            response.raise_for_status()
        metadata = self.cache.store(
            "copernicus-cdse-stac",
            source_uri,
            response.content,
            dict(response.headers),
            response.status_code,
        )
        return parse_stac_search_response(
            response.content,
            uri=source_uri,
            snapshot_id=metadata.snapshot_id,
        )

    @staticmethod
    def normalize_geomet_feature_collection(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate the minimum OGC API Features envelope before product mapping."""
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("GeoMet response missing features array")
        normalized: list[dict[str, Any]] = []
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                continue
            normalized.append(feature)
        return normalized
