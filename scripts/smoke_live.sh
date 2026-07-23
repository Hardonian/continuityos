#!/usr/bin/env bash
set -Eeuo pipefail
BASE_URL="${1:-http://127.0.0.1:8082}"
health="$(curl -fsS --max-time 10 "$BASE_URL/healthz")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"] == "ok"; assert d["evidence_ledger_valid"] is True' <<<"$health"
sources="$(curl -fsS --max-time 10 "$BASE_URL/v1/sources")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d,list) and len(d) >= 1' <<<"$sources"
verify="$(curl -fsS --max-time 10 "$BASE_URL/v1/evidence/verify")"
python3 -c 'import json,sys; assert json.load(sys.stdin)["valid"] is True' <<<"$verify"
printf 'live smoke passed: %s\n' "$BASE_URL"
