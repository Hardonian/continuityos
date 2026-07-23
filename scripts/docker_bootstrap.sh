#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS="$ROOT/secrets"
ENV_FILE="$ROOT/.env"
mkdir -p "$SECRETS"
if [[ ! -x "$ROOT/.venv/bin/continuityos" ]]; then
  printf 'run scripts/install.sh first to create the local CLI\n' >&2
  exit 1
fi
if [[ ! -f "$SECRETS/evidence-private.pem" || ! -f "$SECRETS/evidence-public.pem" ]]; then
  "$ROOT/.venv/bin/continuityos" generate-evidence-keys "$SECRETS"
fi
if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  python3 - <<PY > "$ENV_FILE"
import secrets
print('CONTINUITYOS_API_KEY=' + secrets.token_urlsafe(32))
print('CONTINUITYOS_OPERATOR_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))
PY
fi
chmod 600 "$ENV_FILE"
printf 'docker bootstrap ready: .env and secrets created outside Git\n'
printf 'verify with: docker compose config\n'
