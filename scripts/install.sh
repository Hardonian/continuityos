#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${CONTINUITYOS_ENV_FILE:-$HOME/.config/continuityos.env}"
DATA_DIR="${CONTINUITYOS_DATA_DIR:-$HOME/.local/share/continuityos}"
SECRETS_DIR="$DATA_DIR/secrets"
VENV="$ROOT/.venv"

command -v python3.12 >/dev/null || { printf 'python3.12 is required\n' >&2; exit 1; }
python3.12 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV/bin/pip" install -e "${ROOT}[dev]" >/dev/null
mkdir -p "$SECRETS_DIR" "$(dirname "$ENV_FILE")"
if [[ ! -f "$SECRETS_DIR/evidence-private.pem" || ! -f "$SECRETS_DIR/evidence-public.pem" ]]; then
  "$VENV/bin/continuityos" generate-evidence-keys "$SECRETS_DIR"
fi
if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  python3 - <<PY >> "$ENV_FILE"
import secrets
print('CONTINUITYOS_ENVIRONMENT=production')
print('CONTINUITYOS_DATA_DIR=$DATA_DIR')
print('CONTINUITYOS_EVIDENCE_PRIVATE_KEY_PATH=$SECRETS_DIR/evidence-private.pem')
print('CONTINUITYOS_EVIDENCE_PUBLIC_KEY_PATH=$SECRETS_DIR/evidence-public.pem')
print('CONTINUITYOS_API_KEY=' + secrets.token_urlsafe(32))
print('CONTINUITYOS_OPERATOR_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))
print('CONTINUITYOS_OUTBOUND_HTTP_ENABLED=false')
PY
fi
chmod 600 "$ENV_FILE"
mkdir -p "$HOME/.config/systemd/user"
for unit in continuityos.service continuityos-caddy-route.service continuityos-caddy-route.timer continuityos-backup.service continuityos-backup.timer; do
  install -m 0644 "$ROOT/deploy/$unit" "$HOME/.config/systemd/user/$unit"
done
systemctl --user daemon-reload
systemctl --user enable --now continuityos.service continuityos-caddy-route.timer continuityos-backup.timer
"$ROOT/scripts/status.sh"
