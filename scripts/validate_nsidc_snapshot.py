from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from continuityos.sources.adapters import parse_nsidc_daily_extent_csv

DEFAULT_URI = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv"
)


def validate_snapshot(path: Path, uri: str) -> dict[str, object]:
    body = path.read_bytes()
    observations = parse_nsidc_daily_extent_csv(
        body,
        uri=uri,
        snapshot_id="manual-validation",
    )
    if not observations:
        raise ValueError("snapshot produced no baseline-qualified observations")
    latest = max(observations, key=lambda item: item.observed_at)
    return {
        "validated_at": datetime.now(UTC).isoformat(),
        "source_id": latest.source_id,
        "source_uri": uri,
        "snapshot_sha256": hashlib.sha256(body).hexdigest(),
        "snapshot_bytes": len(body),
        "parsed_observations": len(observations),
        "latest_observation": {
            "date": latest.observed_at.date().isoformat(),
            "extent_anomaly_million_km2": latest.value,
            "absolute_extent_million_km2": latest.metadata["absolute_extent_million_km2"],
            "baseline_median_million_km2": latest.metadata["baseline_median_million_km2"],
            "baseline_period": latest.metadata["baseline_period"],
            "operability_role": latest.metadata["operability_role"],
        },
        "interpretation_boundary": (
            "Arctic-wide climate context only; not local navigation or route-access evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--uri", default=DEFAULT_URI)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_snapshot(args.snapshot, args.uri)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)


if __name__ == "__main__":
    main()
