from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
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
            signature = base64.b64encode(self.private_key.sign(bytes.fromhex(record_hash))).decode()
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

    def _last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "0" * 64
        last_line = self.path.read_text().splitlines()[-1]
        return EvidenceRecord.model_validate_json(last_line).record_hash

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
