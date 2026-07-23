#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from continuityos.analysis import RegressionRequest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a provenance-bearing ContinuityOS regression dataset"
    )
    parser.add_argument("input", type=Path, help="JSON file containing a RegressionRequest")
    parser.add_argument("--output", type=Path, help="optional normalized JSON output path")
    args = parser.parse_args()
    request = RegressionRequest.model_validate_json(args.input.read_text())
    normalized = request.model_dump(mode="json")
    output = json.dumps(normalized, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end="")
    print(
        f"validated dataset={request.dataset_id} rows={len(request.rows)} "
        f"features={len(request.rows[0].features)} target={request.target_name}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
