#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z "${1:-}" || "${1:-}" == -* ]]; then
  printf 'usage: %s BACKUP.tar.gz[.sha256]\n' "$0" >&2
  exit 2
fi
ARCHIVE="$1"
ARCHIVE="${ARCHIVE%.sha256}"
[[ -f "$ARCHIVE" ]] || { printf 'backup not found: %s\n' "$ARCHIVE" >&2; exit 1; }
CHECKSUM="${ARCHIVE}.sha256"
[[ -f "$CHECKSUM" ]] || { printf 'checksum not found: %s\n' "$CHECKSUM" >&2; exit 1; }
sha256sum --check "$CHECKSUM"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/continuityos-restore-check.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
# Reject path traversal and absolute paths before extracting any archive.
if tar -tzf "$ARCHIVE" | grep -Eq '(^/|(^|/)\.\.(\/|$))'; then
  printf 'unsafe archive path detected\n' >&2
  exit 1
fi
tar -xzf "$ARCHIVE" -C "$TMP"
DATA_NAME="$(basename "${CONTINUITYOS_DATA_DIR:-$HOME/.local/share/continuityos}")"
RESTORED="$TMP/$DATA_NAME"
[[ -d "$RESTORED" ]] || { printf 'restored data directory missing: %s\n' "$RESTORED" >&2; exit 1; }
[[ -f "$RESTORED/evidence/ledger.jsonl" ]] || { printf 'ledger missing in backup\n' >&2; exit 1; }
[[ -f "$RESTORED/state.json" ]] || { printf 'state missing in backup\n' >&2; exit 1; }
printf 'verified=%s\n' "$ARCHIVE"
printf 'bytes=%s\n' "$(stat -c '%s' "$ARCHIVE")"
printf 'restored_tree=%s\n' "$RESTORED"
