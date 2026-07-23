#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

output="$(uv run python scripts/demo.py)"
OUTPUT="$output" python - <<'PY'
import json
import os

payload = json.loads(os.environ["OUTPUT"])
assert set(payload) == {"assessment", "plan", "dependency_impact"}
assert payload["plan"]["approval_required"] is True
assert payload["dependency_impact"]["failed_nodes"] == ["shared-idp"]
print("continuityos_demo=PASS")
PY
