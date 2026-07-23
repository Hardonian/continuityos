#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from continuityos.public_data import PUBLIC_SOURCE_SPECS, PublicDataPlane
from continuityos.sources.cache import SnapshotCache


async def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch allow-listed public ContinuityOS snapshots")
    parser.add_argument("--enable-outbound", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=Path(".continuityos-public-cache"))
    parser.add_argument("--source", action="append", dest="sources")
    args = parser.parse_args()
    if not args.enable_outbound:
        parser.error("refusing network access without --enable-outbound")
    source_ids = args.sources or sorted(PUBLIC_SOURCE_SPECS)
    unknown = sorted(set(source_ids) - set(PUBLIC_SOURCE_SPECS))
    if unknown:
        parser.error(f"unknown source(s): {', '.join(unknown)}")
    plane = PublicDataPlane(SnapshotCache(args.cache_dir), outbound_enabled=True)
    results: list[dict[str, object]] = []
    for source_id in source_ids:
        try:
            snapshot = await plane.fetch(source_id)
            results.append(
                {
                    "source_id": snapshot.source_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "sha256": snapshot.content_sha256,
                    "status_code": snapshot.status_code,
                    "record_count": snapshot.record_count,
                    "quality_flags": list(snapshot.quality_flags),
                }
            )
        except Exception as exc:
            results.append(
                {"source_id": source_id, "error_type": type(exc).__name__, "error": str(exc)}
            )
    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0 if all("error" not in item for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
