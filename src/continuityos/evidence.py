from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    record_type: str
    subject_id: str
    payload: dict[str, Any]
    previous_hash: str
    record_hash: str
    signature: str | None = None
    signing_key_id: str | None = None


class EvidenceLedger:
    """Append-only JSONL hash chain with optional Ed25519 signatures."""

    def __init__(
        self,
        path: Path,
        private_key: Ed25519PrivateKey | None = None,
        public_key: Ed25519PublicKey | None = None,
    ) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        self.lock_path.touch(exist_ok=True)
        self.private_key = private_key
        self.public_key = public_key or (private_key.public_key() if private_key else None)

    @classmethod
    def from_key_files(
        cls, path: Path, private_key_path: Path | None, public_key_path: Path | None
    ) -> EvidenceLedger:
        private_key: Ed25519PrivateKey | None = None
        public_key: Ed25519PublicKey | None = None
        if private_key_path:
            private_key = cast(
                Ed25519PrivateKey,
                serialization.load_pem_private_key(private_key_path.read_bytes(), password=None),
            )
            if not isinstance(private_key, Ed25519PrivateKey):
                raise TypeError("private key must be Ed25519")
        if public_key_path:
            public_key = cast(
                Ed25519PublicKey, serialization.load_pem_public_key(public_key_path.read_bytes())
            )
            if not isinstance(public_key, Ed25519PublicKey):
                raise TypeError("public key must be Ed25519")
        return cls(path, private_key, public_key)

    def append(self, record_type: str, subject_id: str, payload: dict[str, Any]) -> EvidenceRecord:
        with self._exclusive_lock():
            previous_hash = self._last_hash()
            unsigned: dict[str, Any] = {
                "record_id": str(uuid4()),
                "created_at": datetime.now(UTC).isoformat(),
                "record_type": record_type,
                "subject_id": subject_id,
                "payload": payload,
                "previous_hash": previous_hash,
            }
            canonical = self._canonical(unsigned)
            record_hash = hashlib.sha256(canonical).hexdigest()
            signature = None
            key_id = None
            if self.private_key is not None:
                signature = base64.b64encode(
                    self.private_key.sign(bytes.fromhex(record_hash))
                ).decode()
                public_bytes = self.private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw,
                )
                key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
            record = EvidenceRecord(
                **unsigned,
                record_hash=record_hash,
                signature=signature,
                signing_key_id=key_id,
            )
            self._append_atomic(record.model_dump_json().encode() + b"\n")
            return record

    def verify(self) -> list[str]:
        errors: list[str] = []
        previous = "0" * 64
        if not self.path.exists():
            return errors
        for index, line in enumerate(self.path.read_text().splitlines(), start=1):
            try:
                record = EvidenceRecord.model_validate_json(line)
            except Exception as exc:
                errors.append(f"line {index}: invalid record: {exc}")
                continue
            if record.previous_hash != previous:
                errors.append(f"line {index}: previous hash mismatch")
            unsigned = {
                "record_id": record.record_id,
                "created_at": record.created_at,
                "record_type": record.record_type,
                "subject_id": record.subject_id,
                "payload": record.payload,
                "previous_hash": record.previous_hash,
            }
            expected = hashlib.sha256(self._canonical(unsigned)).hexdigest()
            if expected != record.record_hash:
                errors.append(f"line {index}: record hash mismatch")
            if record.signature:
                if self.public_key is None:
                    errors.append(f"line {index}: signature present but no public key configured")
                else:
                    try:
                        self.public_key.verify(
                            base64.b64decode(record.signature), bytes.fromhex(record.record_hash)
                        )
                    except Exception:
                        errors.append(f"line {index}: signature verification failed")
            previous = record.record_hash
        return errors

    def records(self, offset: int = 0, limit: int = 100) -> list[EvidenceRecord]:
        """Read a bounded immutable snapshot for export consumers."""
        if offset < 0 or limit < 1 or limit > 1000:
            raise ValueError("offset must be non-negative and limit must be between 1 and 1000")
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if offset >= len(lines):
            return []
        return [EvidenceRecord.model_validate_json(line) for line in lines[offset : offset + limit]]

    def get_record(self, record_id: str) -> EvidenceRecord | None:
        """Find an evidence record by its record_id."""
        if not self.path.exists():
            return None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                rec = EvidenceRecord.model_validate_json(line)
                if rec.record_id == record_id:
                    return rec
            except Exception:
                continue
        return None

    def find_conflicts(self) -> list[dict[str, Any]]:
        """Identify conflicting evidence records without discarding any evidence.

        Invariant 3 & Invariant 6: All provenance is preserved; conflicting
        evidence is explicitly surfaced and explainable.
        """
        if not self.path.exists():
            return []

        all_records = [
            EvidenceRecord.model_validate_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        by_subject: dict[str, list[EvidenceRecord]] = {}
        for rec in all_records:
            by_subject.setdefault(rec.subject_id, []).append(rec)

        conflicts: list[dict[str, Any]] = []

        for subject_id, recs in by_subject.items():
            # Check for conflicting metric values in observations
            obs_by_metric: dict[str, list[EvidenceRecord]] = {}
            for r in recs:
                if r.record_type == "observation" and "metric" in r.payload:
                    obs_by_metric.setdefault(str(r.payload["metric"]), []).append(r)

            for metric, m_recs in obs_by_metric.items():
                if len(m_recs) >= 2:
                    values = [float(r.payload.get("value", 0.0)) for r in m_recs]
                    min_val = min(values)
                    max_val = max(values)
                    if min_val > 0 and (max_val - min_val) / min_val > 0.2:
                        conflicts.append(
                            {
                                "subject_id": subject_id,
                                "conflict_type": "metric_discrepancy",
                                "metric": metric,
                                "spread": round(max_val - min_val, 4),
                                "records": [
                                    {
                                        "record_id": r.record_id,
                                        "source": r.payload.get("source_id", "unknown"),
                                        "value": r.payload.get("value"),
                                        "confidence": r.payload.get("confidence", 1.0),
                                        "created_at": r.created_at,
                                    }
                                    for r in m_recs
                                ],
                                "divergence": f"Observed values for {metric} differ by {((max_val - min_val) / min_val):.1%}",
                                "resolution_note": "Both records preserved in immutable ledger for human review.",
                            }
                        )

            # Check for conflicting corridor states
            state_recs = [r for r in recs if "state" in r.payload or "effective_state" in r.payload]
            if len(state_recs) >= 2:
                states = {
                    str(r.payload.get("state") or r.payload.get("effective_state"))
                    for r in state_recs
                }
                if len(states) > 1:
                    conflicts.append(
                        {
                            "subject_id": subject_id,
                            "conflict_type": "state_conflict",
                            "conflicting_states": sorted(states),
                            "records": [
                                {
                                    "record_id": r.record_id,
                                    "state": r.payload.get("state")
                                    or r.payload.get("effective_state"),
                                    "created_at": r.created_at,
                                }
                                for r in state_recs
                            ],
                            "divergence": f"Subject has conflicting assessed states: {', '.join(sorted(states))}",
                            "resolution_note": "Multi-source evidence divergence preserved for auditability.",
                        }
                    )

        return conflicts

    def _last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "0" * 64
        # Read only the last line by seeking from end of file to avoid loading
        # the entire ledger into memory for large evidence chains.
        with self.path.open("rb") as fh:
            fh.seek(0, 2)  # seek to end
            pos = fh.tell()
            if pos == 0:
                return "0" * 64
            # Walk backwards to find the last newline before the final line
            buf = b""
            while pos > 0:
                read_size = min(4096, pos)
                pos -= read_size
                fh.seek(pos)
                chunk = fh.read(read_size)
                buf = chunk + buf
                # We need at least one complete line (ending with \n followed by content)
                lines = buf.split(b"\n")
                # Filter empty trailing element from trailing newline
                non_empty = [line for line in lines if line.strip()]
                if non_empty:
                    last_line = non_empty[-1].decode("utf-8")
                    return EvidenceRecord.model_validate_json(last_line).record_hash
        return "0" * 64

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> bytes:
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()

    def _append_atomic(self, data: bytes) -> None:
        existing = self.path.read_bytes() if self.path.exists() else b""
        fd, temporary_name = tempfile.mkstemp(dir=self.path.parent, prefix=".ledger-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(existing)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        with self.lock_path.open("a+") as lock_handle:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    lock_handle.seek(0)
                    msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
