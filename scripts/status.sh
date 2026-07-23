#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${CONTINUITYOS_ENV_FILE:-$HOME/.config/continuityos.env}"
printf '%s\n' 'ContinuityOS status'
printf 'repo=%s\n' "$ROOT"
printf 'branch=%s\n' "$(git -C "$ROOT" branch --show-current)"
printf 'commit=%s\n' "$(git -C "$ROOT" rev-parse --short HEAD)"
printf 'service='; systemctl --user is-active continuityos.service || true
printf 'route_timer='; systemctl --user is-active continuityos-caddy-route.timer || true
printf 'listener='; ss -ltn '( sport = :8082 )' | tail -n +2 | tr '\n' ' '; printf '\n'
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi
curl -fsS --max-time 10 http://127.0.0.1:8082/healthz
printf '\n'
