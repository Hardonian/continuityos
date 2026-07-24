#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from continuityos.public_data import DFOIWLSAdapter, ECCCGeoMetAdapter, PublicDataPlane
from continuityos.sources.cache import SnapshotCache


async def main() -> int:
    parser = argparse.ArgumentParser(description="Probe normalized Canadian public indicators")
    parser.add_argument("--enable-outbound", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path(".continuityos-indicator-cache"))
    parser.add_argument("--region", default="QUE", choices=["ATL", "QUE", "PAC", "CNA"])
    args = parser.parse_args()
    if not args.enable_outbound:
        parser.error("refusing network access without --enable-outbound")
    plane = PublicDataPlane(SnapshotCache(args.cache_dir), outbound_enabled=True)
    eccc_snapshot, alerts = await ECCCGeoMetAdapter.fetch(plane)
    end = datetime.now(UTC).replace(second=0, microsecond=0)
    start = end - timedelta(hours=2)
    station_snapshot, data_snapshot, station, water = await DFOIWLSAdapter.fetch_current(
        plane, region=args.region, start=start, end=end
    )
    print(
        json.dumps(
            {
                "eccc": {
                    "snapshot_id": eccc_snapshot.snapshot_id,
                    "indicator_count": len(alerts),
                    "indicator_ids": sorted({item.indicator_id for item in alerts}),
                    "quality_flag_counts": sorted(
                        {flag for item in alerts for flag in item.quality_flags}
                    ),
                },
                "dfo": {
                    "station_snapshot_id": station_snapshot.snapshot_id,
                    "data_snapshot_id": data_snapshot.snapshot_id,
                    "station_id": station["id"],
                    "station_code": station.get("code"),
                    "station_name": station.get("officialName"),
                    "indicator_count": len(water),
                    "observations": [
                        {
                            "observed_at": item.observed_at.isoformat(),
                            "value": item.value,
                            "unit": item.unit,
                            "quality_flags": list(item.quality_flags),
                            "qc_flag_code": item.metadata["qc_flag_code"],
                        }
                        for item in water
                    ],
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
