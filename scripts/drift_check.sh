#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_UNITS="$HOME/.config/systemd/user"
failures=0
check_unit() {
  local name="$1"
  local source="$ROOT/deploy/$name"
  local installed="$USER_UNITS/$name"
  if [[ ! -f "$installed" ]]; then
    printf 'FAIL missing installed unit %s\n' "$name"
    failures=$((failures + 1))
  elif cmp -s "$source" "$installed"; then
    printf 'PASS unit synchronized %s\n' "$name"
  else
    printf 'FAIL unit drift %s\n' "$name"
    failures=$((failures + 1))
  fi
}

printf 'ContinuityOS deployment drift check\n'
printf 'repo=%s\ncommit=%s\n' "$ROOT" "$(git -C "$ROOT" rev-parse HEAD)"
check_unit continuityos.service
check_unit continuityos-backup.service
check_unit continuityos-backup.timer
check_unit continuityos-caddy-route.service
check_unit continuityos-caddy-route.timer
printf 'failures=%s\n' "$failures"
(( failures == 0 ))
