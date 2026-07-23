#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${1:-}" != "--confirm" || -z "${2:-}" ]]; then
  printf 'usage: %s --confirm BACKUP.tar.gz\n' "$0" >&2
  exit 2
fi
ARCHIVE="$2"
DATA_DIR="${CONTINUITYOS_DATA_DIR:-$HOME/.local/share/continuityos}"
[[ -f "$ARCHIVE" ]] || { printf 'backup not found: %s\n' "$ARCHIVE" >&2; exit 1; }
if [[ -f "$ARCHIVE.sha256" ]]; then
  sha256sum --check "$ARCHIVE.sha256"
fi
PARENT="$(dirname "$DATA_DIR")"
mkdir -p "$PARENT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -d "$DATA_DIR" ]]; then
  mv "$DATA_DIR" "${DATA_DIR}.before-restore-$STAMP"
fi
tar -xzf "$ARCHIVE" -C "$PARENT"
printf 'restored=%s\n' "$DATA_DIR"
printf 'previous_data=%s.before-restore-%s\n' "$DATA_DIR" "$STAMP"
