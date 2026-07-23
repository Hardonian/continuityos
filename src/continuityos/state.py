from __future__ import annotations

import fcntl
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class IdempotencyConflict(ValueError):
    """The same idempotency key was reused for a different request."""


class PersistentState:
    """Small locked JSON state store for the single-process reference deployment.

    This is intentionally not a replacement for a transactional customer database.
    It prevents replay across restarts on the documented one-worker deployment and
    provides a clear migration boundary when the first customer workload arrives.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _lock(self) -> Iterator[None]:
        with self.lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"state file is unreadable: {self.path}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"state file must contain an object: {self.path}")
        return value

    def _write_unlocked(self, value: dict[str, Any]) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def get_idempotent(self, namespace: str, key: str, fingerprint: str) -> str | None:
        with self._lock():
            records = self._read_unlocked().setdefault("idempotency", {})
            record = records.get(f"{namespace}:{key}")
            if record is None:
                return None
            if not isinstance(record, dict) or record.get("fingerprint") != fingerprint:
                raise IdempotencyConflict("idempotency key was reused for a different request")
            response = record.get("response")
            if not isinstance(response, str):
                raise RuntimeError("idempotency record has no response")
            return response

    def save_idempotent(self, namespace: str, key: str, fingerprint: str, response: str) -> None:
        with self._lock():
            state = self._read_unlocked()
            records = state.setdefault("idempotency", {})
            existing = records.get(f"{namespace}:{key}")
            if existing is not None and existing.get("fingerprint") != fingerprint:
                raise IdempotencyConflict("idempotency key was reused for a different request")
            records[f"{namespace}:{key}"] = {"fingerprint": fingerprint, "response": response}
            self._write_unlocked(state)

    def claim_sequence(self, tenant_id: str, asset_id: str, sequence: int) -> bool:
        key = f"{tenant_id}:{asset_id}"
        with self._lock():
            state = self._read_unlocked()
            sequences = state.setdefault("telemetry_sequences", {})
            previous = sequences.get(key)
            if previous is not None and sequence <= int(previous):
                return False
            sequences[key] = sequence
            self._write_unlocked(state)
            return True
