#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT="${CONTINUITYOS_DOCTOR_REPORT:-/tmp/continuityos-go-live-doctor.txt}"
PORT="${CONTINUITYOS_PORT:-8082}"
BASE="http://127.0.0.1:${PORT}"
failures=0

pass() { printf 'PASS %s\n' "$*" | tee -a "$REPORT"; }
fail() { printf 'FAIL %s\n' "$*" | tee -a "$REPORT"; failures=$((failures + 1)); }
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$label"; else fail "$label"; fi
}

: > "$REPORT"
printf 'ContinuityOS go-live doctor\nroot=%s\nstarted=%s\n' "$ROOT" "$(date --iso-8601=seconds)" >> "$REPORT"

check "repository clean" git -C "$ROOT" diff --quiet
check "service active" systemctl --user is-active --quiet continuityos.service
main_pid="$(systemctl --user show continuityos.service -p MainPID --value)"
listener_pid="$(ss -ltnp 2>/dev/null | awk -v port=":${PORT}" '$4 == "127.0.0.1" port {match($NF,/pid=([0-9]+)/,m); print m[1]; exit}')"
if [[ -n "$main_pid" && "$main_pid" != 0 && "$main_pid" == "$listener_pid" ]]; then
  pass "managed PID owns loopback listener pid=${main_pid}"
else
  fail "managed PID/listener mismatch managed=${main_pid:-none} listener=${listener_pid:-none}"
fi
check "livez" curl -fsS --max-time 10 "$BASE/livez"
check "readyz" curl -fsS --max-time 10 "$BASE/readyz"
check "healthz" curl -fsS --max-time 10 "$BASE/healthz"
check "anonymous protected route rejected" bash -c "test \"\$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 '$BASE/v1/interoperability')\" = 401"
check "environment file mode" bash -c "test \"\$(stat -c '%a' /home/scott/.config/continuityos.env 2>/dev/null || true)\" = 600"
check "backup timer active" systemctl --user is-active --quiet continuityos-backup.timer
check "Terraform/IaC policy" bash "$ROOT/scripts/iac_verify.sh"
check "tracked secret scan" bash -c "matches=\$(git -C '$ROOT' grep -IlE -- '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|sk_live_[A-Za-z0-9]|whsec_[A-Za-z0-9]' -- ':!tests' || true); test -z \"\$matches\""

printf 'main_pid=%s\nlistener_pid=%s\nfinished=%s\nfailures=%s\nreport=%s\n' \
  "$main_pid" "$listener_pid" "$(date --iso-8601=seconds)" "$failures" "$REPORT" | tee -a "$REPORT"
(( failures == 0 ))
