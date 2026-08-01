#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${CONTINUITYOS_DATA_DIR:-$HOME/.local/share/continuityos}"
BACKUP_DIR="${CONTINUITYOS_BACKUP_DIR:-$DATA_DIR/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/continuityos-$STAMP.tar.gz"
mkdir -p "$BACKUP_DIR"
if [[ ! -d "$DATA_DIR" ]]; then
  printf 'no data directory: %s\n' "$DATA_DIR" >&2
  exit 1
fi
# Never place the backup directory inside the archived tree. The host-exposure
# audit is root-owned generated output, not ContinuityOS state; excluding it keeps
# the non-root backup job fail-closed instead of producing a partial archive.
# shellcheck disable=SC2016
EXCLUDES=(
  --exclude="$(basename "$BACKUP_DIR")"
  --exclude="$(basename "$DATA_DIR")/host-exposure-audit.txt"
)
tar -C "$(dirname "$DATA_DIR")" "${EXCLUDES[@]}" -czf "$ARCHIVE" "$(basename "$DATA_DIR")"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
chmod 600 "$ARCHIVE" "$ARCHIVE.sha256"
tar -tzf "$ARCHIVE" >/dev/null
find "$BACKUP_DIR" -type f -name 'continuityos-*.tar.gz' -mtime +14 -delete
find "$BACKUP_DIR" -type f -name 'continuityos-*.tar.gz.sha256' -mtime +14 -delete
printf 'backup=%s\n' "$ARCHIVE"
